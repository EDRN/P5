# EDRN Portal Architecture

The Early Detection Research Network (EDRN) public portal is a [Wagtail](https://wagtail.org/) CMS on [Django](https://www.djangoproject.com/). It is the software that nominally runs [edrn.cancer.gov](https://edrn.cancer.gov/). The codebase is a composition of Python packages.

This document is a high-level map of how those packages, services, and external systems fit together. Docker-specific runtime wiring is also covered in [`docker/architecture-diagram.md`](../docker/architecture-diagram.md).

---

## Runtime stack

Visitors hit a reverse proxy (ALB, Nginx, or Apache). That proxy serves static and media files from the host filesystem and forwards everything else to Gunicorn, which runs the Django/Wagtail application. A Celery worker shares the same image and database and handles long-running work (RDF ingest, search reindex, LDAP group sync, email).

```mermaid
flowchart TB
    Users[Visitors and editors]
    Proxy[Reverse proxy<br/>ALB / Nginx / Apache]
    Portal[Portal process<br/>Gunicorn + Django / Wagtail]
    Worker[Celery worker<br/>same image, django-admin worker]

    PG[(PostgreSQL<br/>pages, users, ingest state)]
    Redis[(Redis<br/>cache, locks, Celery broker)]
    ES[(Elasticsearch<br/>Wagtail search index)]

    LDAP[EDRN Directory<br/>ldaps://edrn-ds.jpl.nasa.gov]
    RDF[EDRN RDF sources<br/>DMCC / LabCAS / knowledge feeds]
    NCBI[NCBI Entrez / PubMed]
    AWS[AWS<br/>Location Service, Bedrock]
    Email[NIH mail relay]
    Census[US Census geocoder]

    Users --> Proxy
    Proxy -->|/static, /media| Files[(Host volumes<br/>static + media)]
    Proxy -->|everything else| Portal

    Portal --> PG
    Portal --> Redis
    Portal --> ES
    Worker --> PG
    Worker --> Redis
    Worker --> ES
    Worker --> Files

    Portal --> LDAP
    Portal --> Email
    Portal --> AWS
    Worker --> RDF
    Worker --> NCBI
    Worker --> AWS
    Worker --> Census
    Worker --> Email
```

`edrnsite.policy.settings.ops` is the production settings module. Local development uses `local.py`, which imports `edrnsite.policy.settings.dev`.

---

## Python packages

`edrnsite.policy` is the composition root: Django settings, root URLConf, WSGI entry, Celery app, and management commands. Everything else is a Django/Wagtail app. `edrn.auth` is an external package (not in this repo) that supplies login views and the `logged_in_or_basicauth` decorator used by staff-only endpoints.

```mermaid
flowchart TB
    subgraph composition ["Composition"]
        policy["edrnsite.policy<br/>settings, URLs, WSGI, Celery, ops commands"]
        test["edrnsite.test<br/>Selenium smoke tests, dev only"]
    end

    subgraph presentation ["Site chrome and CMS content"]
        theme["edrn.theme<br/>templates, menus, look and feel"]
        content["edrnsite.content<br/>HomePage, FlexPage, forms"]
        streams["edrnsite.streams<br/>StreamField blocks, CDE explorer"]
        collab["edrn.collabgroups<br/>Committee pages and events"]
        search["edrnsite.search<br/>/search, AI summarize"]
        metrics["edrn.metrics<br/>data-quality reports"]
        controls["edrnsite.controls<br/>site settings, analytics, social"]
    end

    subgraph knowledge ["Knowledge environment"]
        knowledgeApp["eke.knowledge<br/>sites, people, protocols, pubs, data"]
        biomarkers["eke.biomarkers<br/>biomarker pages"]
        geocoding["eke.geocoding<br/>address cache, AWS / Census"]
    end

    subgraph support ["Supporting"]
        auth["edrn.auth<br/>external: login / basic auth"]
        plone["edrnsite.ploneimport<br/>one-time Plone → Wagtail import"]
    end

    policy --> theme
    policy --> content
    policy --> search
    policy --> knowledgeApp
    policy --> biomarkers
    policy --> metrics
    policy --> controls
    policy --> collab
    policy --> plone
    policy --> auth
    test --> content
    test --> controls

    theme --> controls
    theme --> auth
    content --> streams
    collab --> streams
    collab --> content
    search --> controls
    metrics --> auth

    knowledgeApp --> content
    knowledgeApp --> controls
    knowledgeApp --> collab
    knowledgeApp --> geocoding
    biomarkers --> knowledgeApp
    biomarkers --> content
    biomarkers --> auth
```

Install order in the root `README.md` (geocoding → streams → controls → content → collabgroups → knowledge → biomarkers → search → theme → ploneimport → metrics → policy → test) follows these dependencies.

---

## Request flow

`edrnsite.policy.urls` concatenates app URL patterns, then Wagtail's page tree. Dedicated Django views sit in front of the catch-all Wagtail page router.

```mermaid
flowchart LR
    Req[HTTP request] --> URLs["edrnsite.policy.urls"]

    URLs --> Streams["edrnsite.streams<br/>update_data_element_explorers"]
    URLs --> Controls["edrnsite.controls<br/>update_my_ip"]
    URLs --> Knowledge["eke.knowledge<br/>ingest, reindex, find-members,<br/>dataDispatch, Plotly Dash"]
    URLs --> Search["edrnsite.search<br/>/search, /summarize"]
    URLs --> Auth["edrn.auth<br/>login / logout"]
    URLs --> Metrics["edrn.metrics<br/>run-data-quality-report"]
    URLs --> Admin["/admin Wagtail<br/>/django-admin Django"]
    URLs --> Pages["Wagtail page tree<br/>HomePage, FlexPage,<br/>KnowledgeObject, …"]

    Search --> ES[(Elasticsearch)]
    Search --> Bedrock[Amazon Bedrock]
    Knowledge --> Celery[Celery tasks]
    Pages --> PG[(PostgreSQL)]
    Pages --> Theme["edrn.theme templates"]
```

Staff-only operational URLs (`start_full_ingest`, `reindex_all_content`, `sync_ldap_groups`, `fixtree`, and similar) enqueue Celery tasks rather than doing the work in the request.

---

## Knowledge ingest

Knowledge pages are Wagtail pages with RDF subject URIs. Each `KnowledgeFolder` points at one or more `RDFSource` URLs. A full ingest walks enabled folders in `ingest_order`, maps RDF predicates to model fields, then repairs the page tree and rebuilds the search index.

```mermaid
sequenceDiagram
    participant Admin as Staff / scheduler
    participant Portal as Portal views
    participant Redis as Redis lock
    participant Worker as Celery worker
    participant RDF as RDF HTTP sources
    participant PG as PostgreSQL
    participant NCBI as NCBI Entrez
    participant ES as Elasticsearch

    Admin->>Portal: GET /start_full_ingest
    Portal->>Worker: do_full_ingest.delay()
    Worker->>Redis: acquire full_ingest lock
    Worker->>PG: KnowledgeFolder.objects ingest=True
    loop each folder by ingest_order
        Worker->>RDF: Graph.parse(RDFSource.url)
        Worker->>PG: create / update / delete KnowledgeObjects
        opt publications
            Worker->>NCBI: Entrez metadata / abstracts
        end
        opt sites
            Worker->>Worker: geocode investigator addresses
        end
    end
    Worker->>PG: fixtree
    Worker->>ES: wagtail_update_index
    Worker->>Redis: release lock
```

`eke.knowledge.utils.Ingestor` is the base mapper. Folders can substitute a custom ingestor (committees populate `edrn.collabgroups.Committee` rather than a knowledge object). Biomarker ingest lives in `eke.biomarkers` and uses the same RDF folder pattern.

Other Celery tasks:

| Task | Package | Purpose |
|---|---|---|
| `do_full_ingest` | `eke.knowledge` | RDF ingest of all enabled folders |
| `do_reindex` | `eke.knowledge` | Rebuild Wagtail search index |
| `do_fix_tree` | `eke.knowledge` | Wagtail `fixtree` |
| `do_ldap_group_sync` | `eke.knowledge` | Copy LDAP groups into Django |
| `do_update_my_ip` | `edrnsite.controls` | Record the portal's egress IP |
| `do_send_email` | `edrnsite.content` | Delayed form-notification email |

---

## Domain: pages and knowledge

Editorial content and ingested knowledge both live in Wagtail's page tree. Knowledge types share `KnowledgeObject` (an RDF subject URI plus description) and sit under typed index folders.

```mermaid
flowchart TB
    subgraph cms ["Editorial CMS — edrnsite.content"]
        Home[HomePage]
        Section[SectionPage]
        Flex[FlexPage]
        Forms["Email / captcha forms<br/>biomarker submission<br/>specimen reference set<br/>dataset metadata"]
        Postman[PostmanAPIPage]
    end

    subgraph ke ["Knowledge objects — eke.knowledge"]
        KO[KnowledgeObject]
        Site[Site]
        Person[Person]
        Protocol[Protocol]
        Pub[Publication]
        Data[DataCollection]
        Disease[Disease]
        Body[BodySystem]
        Misc[MiscellaneousResource]
        Finder[MemberFinderPage]
    end

    subgraph bm ["eke.biomarkers"]
        BM[Biomarker]
        BMBS[BiomarkerBodySystem]
    end

    subgraph cg ["edrn.collabgroups"]
        Committee[Committee]
        Event[CommitteeEvent]
    end

    Home --> Section
    Section --> Flex
    Section --> Forms
    Flex --> streamsNote["StreamField blocks from edrnsite.streams"]

    KO --> Site
    KO --> Person
    KO --> Protocol
    KO --> Pub
    KO --> Data
    KO --> Disease
    KO --> Body
    KO --> Misc
    KO --> BM

    Protocol --> Site
    Protocol --> Pub
    Protocol --> Disease
    Site --> Person
    BM --> Protocol
    BM --> Pub
    BM --> Data
    BM --> BMBS
    Committee --> Person
    Committee --> Event
```

`@@dataDispatch?subjectURI=…` is a compatibility shim: given an RDF identifier, it redirects to the matching knowledge page.

---

## Configuration and identity

Authentication tries LDAP first (`django_auth_ldap`), then Django's model backend. Wagtail password management is disabled; credentials live in the EDRN Directory. Site-wide knobs are Wagtail settings, not code:

| Setting | App | Role |
|---|---|---|
| `Informatics` | `edrnsite.controls` | Entrez identity, DMCC URL, banner, version override |
| `Search` | `edrnsite.controls` | Pagination plus Bedrock credentials / prompt |
| `RDFIngest` | `eke.knowledge` | Global ingest enable, timeout, protocol ID cutoff |
| `Geocoding` | `eke.geocoding` | AWS Location Service keys |

`edrnsite.test` is not installed in the production image. It is a Firefox/Selenium suite aimed at a running portal (`task e2e`).
