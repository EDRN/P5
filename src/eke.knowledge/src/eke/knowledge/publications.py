# encoding: utf-8

from .constants import MAX_URI_LENGTH, MAX_SLUG_LENGTH
from .knowledge import KnowledgeObject, KnowledgeFolder, DataTableColumn, DataTableOrdering
from .utils import edrn_schema_uri as esu
from .utils import Ingestor as BaseIngestor
from Bio import Entrez
from contextlib import closing
from django.db import models
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.text import slugify
from django_plotly_dash import DjangoDash
from edrnsite.controls.models import Informatics
from html import escape as html_escape
from http.client import HTTPException
from modelcluster.fields import ParentalKey
from plotly.express import bar
from rdflib import URIRef
from urllib.error import HTTPError
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable
from wagtail.models import Site as WagtailSite
from wagtail.search import index
import dash_core_components as dcc
import dash_html_components as html
import pandas, re, logging, rdflib, time, random


_logger = logging.getLogger(__name__)


class PMCID(models.Model):
    pmid = models.CharField(max_length=20, blank=True, null=False, help_text='Entrez Medline PMID code number')
    pmcid = models.CharField(max_length=20, blank=True, null=False, help_text='Entrez Medline PMCID code number')
    class Meta:
        indexes = [
            models.Index(fields=['pmid'])
        ]


class Publication(KnowledgeObject):
    template = 'eke.knowledge/publication.html'
    parent_page_types = ['ekeknowledge.PublicationIndex']
    page_description = 'Article, column, book, etc., of published scientific research'
    issue = models.CharField(max_length=50, blank=True, null=False, help_text='In what issue publication appeared')
    volume = models.CharField(max_length=50, blank=True, null=False, help_text='In what volume publication appeared')
    journal = models.CharField(max_length=250, blank=True, null=False, help_text='Name of the periodical')
    pubMedID = models.CharField(max_length=20, blank=True, null=False, help_text='Entrez Medline ID code number')
    year = models.IntegerField(blank=True, null=True, help_text='Year of publication')
    pubURL = models.URLField(blank=True, null=False, help_text='URL to read the publication')

    # siteID should be deleted and use the site_that_wrote_this relation instead
    siteID = models.CharField(
        max_length=MAX_URI_LENGTH, blank=True, null=False,
        help_text='RDF subject URI of site that wrote the publication'
    )

    abstract = RichTextField(
        'abstract',
        blank=True, null=False,
        help_text='A summary of the contents of this publication'
    )

    def data_table(self) -> dict:
        '''Return the JSON-compatible dictionary describing this publication.'''
        return {'journal': self.journal, 'year': self.year, **super().data_table()}

    def get_context(self, request: HttpRequest, *args, **kwargs) -> dict:
        context = super().get_context(request, args, kwargs)
        appearances = []
        if self.journal: appearances.append(self.journal)
        if self.year: appearances.append(str(self.year))
        if self.volume: appearances.append(self.volume)
        appearances = ', '.join(appearances)
        if self.issue: appearances += ' ({})'.format(html_escape(self.issue))
        context['appearance'] = appearances
        return context
    content_panels = KnowledgeObject.content_panels + [
        FieldPanel('issue'),
        FieldPanel('volume'),
        FieldPanel('journal'),
        FieldPanel('pubMedID'),
        FieldPanel('year'),
        FieldPanel('pubURL'),
        FieldPanel('abstract'),
        InlinePanel('authors', label='Authors')
    ]
    search_fields = KnowledgeObject.search_fields + [
        # index.SearchField('abstract', partial_match=False),  # See if we can get biomarkers higher
        index.RelatedFields('authors', [index.SearchField('value')]),
        index.SearchField('journal'),
        index.FilterField('journal'),
        index.FilterField('year')
    ]
    class Meta:
        indexes = [models.Index(fields=['pubMedID']), models.Index(fields=['year'])]
    # Publications are special in that they don't use the RDFMeta and standard ingest "plumbing"
    # class RDFMeta:
    #     fields = {
    #         esu('year'): RDFAttribute('year', scalar=True),
    #         str(rdflib.DCTERMS.creator): RDFAttribute('authors', scalar=False, rel=False),
    #         **KnowledgeObject.RDFMeta.fields
    #     }


class PublicationSubjectURI(Orderable):
    '''An RDF subject URI that is used to refer to a single publication.'''
    identifier = models.CharField(
        'Subject URI',
        blank=False, null=False, primary_key=False, unique=True, max_length=MAX_URI_LENGTH,
        help_text='RDF subject URI that uniquely identifies this object',
    )
    page = ParentalKey(Publication, on_delete=models.CASCADE, related_name='subject_uris')
    panels = [FieldPanel('identifier')]
    def __str__(self):
        return self.identifier


class Author(Orderable):
    '''An author of a publication.'''
    value = models.CharField(max_length=255, blank=False, null=False, default='Name', help_text='Author name')
    page = ParentalKey(Publication, on_delete=models.CASCADE, related_name='authors')
    panels = [FieldPanel('value')]
    def __str__(self):
        return self.value


class Ingestor(BaseIngestor):
    '''Publications use a special ingest based on PubMedIDs and grant numbers, not the statements made in
    the RDF.
    '''
    _grant_search_size = 17                                                   # How many grants to get at once
    _max_failures      = 5                                                    # Accept no more HTTP failures than this
    _pub_med_predicate = URIRef(esu('pmid'))                                  # RDF predicate for PubMed ID
    _pub_type          = 'http://edrn.nci.nih.gov/rdf/types.rdf#Publication'  # RDF type URI for publications
    _pubmed_fetch_size = 67                                                   # How many pubs to get at once
    _pubmed_pattern    = re.compile(r'[0-9]+')                                # What PubMed IDs should look like
    _site_id_predicate = URIRef(esu('site'))                                  # RDF predicate for site ID
    _wait_time         = 13                                                   # Seconds to wait between hitting API

    # def slugify(self, pubMedID: str, title: str, identifier: str) -> str:
    #     '''Make an appropriate URI slug component for a publication.'''
    #     lastpath = urlparse(identifier).path.split('/')[-1]
    #     return slugify(f'{pubMedID} {lastpath} {title}')[:MAX_SLUG_LENGTH]

    def slugify(self, pubMedID: str, title: str) -> str:
        '''Make an appropriate URI slug component for a publication.'''
        return slugify(f'{pubMedID} {title}')[:MAX_SLUG_LENGTH]

    def configure_entrez(self):
        '''Set up the Entrez API.

        Before we attempt to access Entrez for PubMed info, we need to configure it with our tool ID
        and an email address.
        '''
        informatics = Informatics.for_site(WagtailSite.objects.filter(is_default_site=True).first())
        Entrez.tool = informatics.entrez_id
        Entrez.email = informatics.entrez_email
        if informatics.entrez_api_key:
            Entrez.api_key = informatics.entrez_api_key

    def miriam_uri(self, pmid: str) -> str:
        '''Make a MIRIAM-style PubMed URI for the given ``pmid``.'''
        return f'urn:miriam:pubmed:{pmid}'

    def parse_statements(self, statements: dict) -> tuple:
        '''Parse the ``statements`` and return a triple of a set of discovered pubmed IDs,
        a mapping of pubmed IDs to sets of site RDF URIs, and a mapping of pubmed IDs to sets
        of RDF subject URIs.
        '''
        pmids, pmids_to_sites, pmids_to_uris = set(), dict(), dict()

        # Go through every subject
        for subject, predicates in statements.items():
            # First, make sure it's a publication being described
            kind = predicates.get(rdflib.RDF.type, [''])[0].strip()
            if kind != self._pub_type:
                _logger.warning('Got a non-publication in publication RDF for subject %s; skipping', subject)
                continue

            # Next make sure there's a pubmed ID
            pmid = predicates.get(self._pub_med_predicate, [''])[0].strip()
            if not self._pubmed_pattern.match(pmid):
                _logger.warning('Got a weird "pubmed" ID «%s» for subject %s that I am skipping', pmid, subject)
                continue

            # Good pubmed ID so far
            pmids.add(pmid)

            # Now get the site mentioned, if any. Note that the data from the DMCC is that there's only ever
            # going to be one site, but that doesn't make sense in reality. So on the off chance there's multiple,
            # let's handle that case.
            site_ids = set([str(i).strip() for i in predicates.get(self._site_id_predicate, [])])
            sites_so_far = pmids_to_sites.get(pmid, set())
            sites_so_far |= site_ids
            pmids_to_sites[pmid] = sites_so_far

            # Do the same thing for subject URis
            uris_so_far = pmids_to_uris.get(pmid, set())
            uris_so_far.add(str(subject))
            pmids_to_uris[pmid] = uris_so_far

        return pmids, pmids_to_sites, pmids_to_uris

    def get_pmids_fromt_grants(self) -> set:
        '''Return the pubmed IDs for all the grant numbers specified in this folder.'''

        pmids, last_group = set(), False

        # This list→set→list makes grant numbers unique and in sliceable form:
        grant_numbers = list(set([i.value for i in self.folder.grant_numbers.all()]))
        random.shuffle(grant_numbers)
        if not grant_numbers:
            _logger.info('No grant numbers found in %r; skipping grant number lookup', self.folder)
            return pmids

        # Batching
        def divide():
            '''Divide the grant_numbers in groups for API sensitivty.'''
            nonlocal grant_numbers, last_group
            while len(grant_numbers) > 0:
                group, grant_numbers = grant_numbers[:self._grant_search_size], grant_numbers[self._grant_search_size:]
                if len(grant_numbers) == 0:
                    last_group = True
                yield group

        # Find pmids for grant numbers
        for group in divide():
            _logger.info('Querying Entrez for grants «%r»', group)
            search_term = u' OR '.join([u'({}[Grant Number])'.format(i) for i in group])
            # #80: PubMed API is really unreliable; try to press on even if it fails
            try:
                # FIXME: This'll break if it returns more than 9999 publications 😅
                with closing(Entrez.esearch(db='pubmed', rettype='medline', retmax=9999, term=search_term)) as es:
                    record = Entrez.read(es)
                    if not record: continue
                    found = set(record.get('IdList', []))
                    if not found: continue
                    pmids |= found
                    if last_group:
                        # We're immediately going to do pubmed queries after these grant queries, so wait at
                        # least a little bit after the last group instead of immediately relinquishing control.
                        time.sleep(self._wait_time / 2)
                    else:
                        time.sleep(self._wait_time)
            except (HTTPError, HTTPException) as ex:
                _logger.warning('Entrez search failed for «%s» but pressing on', ex.getcode(), search_term)

        # That's it
        return pmids

    def get_authors(self, record) -> list:
        '''Get the authors from the given medline ``record``.'''
        author_list = record['MedlineCitation']['Article'].get('AuthorList', [])
        names = []
        for author in author_list:
            last_name = author.get('LastName', None)
            if not last_name:
                initials = author.get('Initials', None)
                if not initials: continue
            initials = author.get('Initials', None)
            if last_name and initials:
                name = f'{last_name} {initials}'
            else:
                name = last_name
            names.append(name)
        names.sort()
        return names

    def get_pubmed_details(self, pmids: set) -> dict:
        '''Query Entrez for details about the publications identified in ``pmids``.
        '''

        pmids, last_group, details = list(pmids), False, dict()
        random.shuffle(pmids)

        # Batching
        def divide():
            '''Divide the pubmed IDs into groups for API sensitivity.'''
            nonlocal pmids, last_group
            while len(pmids) > 0:
                group, pmids = pmids[:self._pubmed_fetch_size], pmids[self._pubmed_fetch_size:]
                if len(pmids) == 0:
                    last_group = True
                yield group

        for group in divide():
            failures = 0
            while True:
                try:
                    _logger.info('Querying Entrez for pmids «%r»', group)
                    with closing(Entrez.efetch(db='pubmed', retmode='xml', rettype='medline', id=group)) as ef:
                        records = Entrez.read(ef)
                        for record in records['PubmedArticle']:
                            pubmed_id = str(record['MedlineCitation']['PMID'])
                            title = str(record['MedlineCitation']['Article']['ArticleTitle'])
                            abstract = record['MedlineCitation']['Article'].get('Abstract')
                            if abstract:
                                paragraphs = abstract.get('AbstractText', [])
                                if len(paragraphs) > 0:
                                    abstract = '\n'.join([f'<p>{html_escape(str(j))}</p>' for j in paragraphs])
                                else:
                                    abstract = ''
                            else:
                                abstract = ''
                            issue = str(record['MedlineCitation']['Article']['Journal']['JournalIssue'].get('Issue'))
                            year = str(record['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate'].get('Year'))
                            journal = str(record['MedlineCitation']['Article']['Journal']['ISOAbbreviation'])
                            authors = self.get_authors(record)
                            details[pubmed_id] = (title, abstract, issue, year, journal, authors)
                        break
                except (HTTPError, HTTPException) as ex:
                    failures += 1
                    if failures >= self._max_failures:
                        raise RuntimeError(f'Too many failures ({failures})') from ex
                    _logger.warning('Entrez failed for batch «%r»; will re-attempt', group)
                    if hasattr(ex, 'geturl'):
                        _logger.warning('Entrez failed URL was «%s»', ex.geturl())
                    if hasattr(ex, 'getcode'):
                        _logger.warning('Status code was %d', ex.getcode())
                    time.sleep(self._wait_time)
            if not last_group:
                time.sleep(self._wait_time)
        return details

    def associate_publication(self, publication: Publication, pmids_to_sites: dict, pmids_to_uris: dict):
        '''Associate the ``publication`` with ``Site`` and RDF ``PublicationSubjectURI`` objects.

        Return True if we made any udpates to either, False otherwise.
        '''
        modifications = False

        from .sites import Site
        site_uris = pmids_to_sites.get(publication.pubMedID, set())

        existing_site_uris = set([i for i in publication.site_that_wrote_this.all().values_list('identifier', flat=True)])
        if site_uris != existing_site_uris:
            modifications = True
            publication.site_that_wrote_this.set(Site.objects.filter(identifier__in=site_uris), clear=True)

        subject_uris = pmids_to_uris.get(publication.pubMedID, set())
        existing_subject_uris = set([i for i in publication.subject_uris.all().values_list('identifier', flat=True)])
        if subject_uris != existing_subject_uris:
            modifications = True
            publication.subject_uris.set([PublicationSubjectURI(identifier=i) for i in subject_uris], clear=True)

        if modifications: publication.save()
        return modifications

    def create_new_publications(self, pmids: set, pmids_to_sites: dict, pmids_to_uris: dict) -> set:
        '''Create brand new publication objects for the pubmed IDs in ``pmids``.

        Map those objects to sites in ``pmids_to_sites`` and to subject URIs in ``pmids_to_uris``.
        Return a set of the newly created objects.
        '''
        new_pubs = set()
        details = self.get_pubmed_details(pmids)
        for pmid in pmids:
            deets = details.get(pmid)
            if not deets:
                _logger.warning('No pubmed info found for PMID «%s», cannot create an object for it', pmid)
                continue
            title, abstract, issue, year, journal, authors = deets
            p = Publication(
                # 🔮 Maybe truncate titles better?
                title=title[:255], live=True, slug=self.slugify(pmid, title),
                identifier=self.miriam_uri(pmid), pubMedID=pmid,
                search_description='This is a pbulication by a member of the Early Detection Research Network.'
            )
            self.folder.add_child(instance=p)
            p.save()
            p.authors.add(*[Author(value=i) for i in authors])
            self.associate_publication(p, pmids_to_sites, pmids_to_uris)
            new_pubs.add(p)
        return new_pubs

    def update_existing_publications(self, pmids: set, pmids_to_sites: dict, pmids_to_uris: dict) -> set:
        '''Update existing publication objects for the pubmed IDs in ``pmids``.

        Map those objects to sites in ``pmids_to_sites`` and to subject URIs in ``pmids_to_uris``
        as needed for changes. Note that data from Entrez API is not updated. We assume it's correct
        eternally. If that's not the case, manually delete the publication object and re-ingest.

        Return a set of publication objects that actually got updated. The cardinally of that
        set will always be equal to or lower than the cardinality of ``pmids``, and frequently
        much lower.
        '''
        modified = set()
        for pub in Publication.objects.filter(pubMedID__in=pmids):
            if self.associate_publication(pub, pmids_to_sites, pmids_to_uris):
                modified.add(pub)
        return modified

    def delete_obsolete_publications(self, pmids: set) -> set:
        '''Delete publication objects identified by the given ``pmids``.

        Return the same set.
        '''
        Publication.objects.filter(pubMedID__in=pmids).delete()
        return pmids

    def update_publications(self, pmids: set, pmids_to_sites: dict, pmids_to_uris: dict) -> tuple:
        '''Update publications.

        Go through the currently populated publications and the given set of ``pmids`` to figure out
        the publications to be created, to be updated, and to be deleted. Return a tuple of the
        newly created publications, the updated ones, and the deleted ones.
        '''

        current_pmids = set([i for i in Publication.objects.child_of(self.folder).values_list('pubMedID', flat=True)])
        pmids_to_create = pmids - current_pmids
        pmids_to_update = current_pmids & pmids
        pmids_to_delete = current_pmids - pmids

        new = self.create_new_publications(pmids_to_create, pmids_to_sites, pmids_to_uris)
        updated = self.update_existing_publications(pmids_to_update, pmids_to_sites, pmids_to_uris)
        deleted = self.delete_obsolete_publications(pmids_to_delete)

        return new, updated, deleted

    def ingest(self):
        self.configure_entrez()
        statements = self.readRDF()
        pmids, pmids_to_sites, pmids_to_uris = self.parse_statements(statements)
        pmids |= self.get_pmids_fromt_grants()
        new, updated, deleted = self.update_publications(pmids, pmids_to_sites, pmids_to_uris)
        return new, updated, deleted


class PublicationIndex(KnowledgeFolder):
    '''A publication index is a container for Publications.'''

    template = 'eke.knowledge/publication-index.html'
    subpage_types = [Publication]
    page_description = 'Container for publications'

    # 🔮 TODO: memoize!
    def get_server_side_datatable_results(
        self, search_value: str, columns: list[DataTableColumn], orderings: list[DataTableOrdering]
    ) -> list[dict]:
        '''Get the datatable results for the given search parameters and return them as a
        list of dicts describing each matching row.
        '''
        matches = Publication.objects.child_of(self).live().public()

        # At this point we'd use Q with filter and F with order_by and finally .search() to
        # get a set of matches, however thanks to wagtail/wagtail#5319, we can't do any column
        # ordering after Elasticsearch changes the PageQuerySet into a SearchResults.
        #
        # This means server-side DataTables will have to remain a hoped-for dream.

        return matches

    def get_contents(self, request: HttpRequest):
        '''Get the contents of this folder but only the DMCC curated publications.

        Why oh why is this not appearing in the Docker image?
        '''
        matches = Publication.objects.filter(subject_uris__identifier__startswith='http://edrn.nci.nih.gov/data/pubs/')\
            .child_of(self).live().public().filter(year__isnull=False).order_by('-year')

        journals = request.GET.getlist('journal')
        if journals: matches = matches.filter(journal__in=journals)

        query = request.GET.get('query')
        if query: matches = matches.search(query)

        return matches

    def faceted_markup(self, request):
        pages, rows = self.get_contents(request), []
        for page in pages:
            rows.append(render_to_string('eke.knowledge/publication-row.html', {'publication': page.specific}))
        return ''.join(rows)

    def get_context(self, request: HttpRequest, *args, **kwargs) -> dict:
        context = super().get_context(request, *args, **kwargs)

        byYear = {}
        for publication in context['knowledge_objects']:
            if publication.year:
                count = byYear.get(publication.year, 0)
                count += 1
                byYear[publication.year] = count

        years, counts = [], []
        for year in sorted(byYear.keys()):
            years.append(year)
            counts.append(byYear[year])

        df = pandas.DataFrame({
            "Year": years,
            "# Publications": counts
        })
        figure = bar(df, x='Year', y='# Publications', barmode="group")

        APP_NAME = 'PubsByYear'
        app = DjangoDash(APP_NAME)
        app.layout = html.Div(children=[
            html.H4(children='Publication Frequency by Year'),
            dcc.Graph(id='publications-by-year', figure=figure)
        ])

        return context

    content_panels = KnowledgeFolder.content_panels + [InlinePanel('grant_numbers', label='Grant Numbers')]

    class Meta:
        pass
    class RDFMeta:
        ingestor = Ingestor
        types = {
            'http://edrn.nci.nih.gov/rdf/types.rdf#Publication': Publication,
        }


class GrantNumber(Orderable):
    '''An NIH-assigned funding identifier that identifies additional publications.'''
    value = models.CharField(max_length=20, blank=False, null=False, help_text='Grant Number')
    page = ParentalKey(PublicationIndex, on_delete=models.CASCADE, related_name='grant_numbers')
    panels = [FieldPanel('value')]
