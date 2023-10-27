# Early Detection Research Network Portal

This is the software for the Early Detection Research Network (EDRN) public portal and knowledge environment. It nominally runs the site at https://edrn.nci.nih.gov/


## 🤓 Development

To develop the portal software for the Early Detection Research Network, you'll need Python, PostgreSQL, Elasticsearch, Redis, and a couple of environment variables. Note that these environment variables should be provided in the development environment, by the continuous integration, by the containerization system, etc. They must be set *always*:

| Variable Name        | Use                                                | Value                               |
|----------------------|----------------------------------------------------|-------------------------------------|
| `DATABASE_URL`       | URL to the database where the portal persists data | `postgresql://:@/edrn`              |
| `LDAP_BIND_PASSWORD` | Credential for the EDRN Directory `service` user   | Contact the directory administrator | 

Next, set up a PostgreSQL database:

```console
$ createdb edrn
```

This has to be done just for the first time—or if you ever get rid of the database with `dropdb edrn`. Then, set up the software and database schema and content:

```console
$ python3 -m venv .venv
$ .venv/bin/pip install --quiet --upgrade pip setuptools wheel build
$ .venv/bin/pip install --editable 'src/eke.geocoding[dev]'
$ .venv/bin/pip install --editable 'src/edrnsite.streams[dev]'
$ .venv/bin/pip install --editable 'src/edrnsite.controls[dev]'
$ .venv/bin/pip install --editable 'src/edrnsite.content[dev]'
$ .venv/bin/pip install --editable 'src/edrn.auth[dev]'
$ .venv/bin/pip install --editable 'src/edrn.collabgroups[dev]'
$ .venv/bin/pip install --editable 'src/eke.knowledge[dev]'
$ .venv/bin/pip install --editable 'src/eke.biomarkers[dev]'
$ .venv/bin/pip install --editable 'src/edrnsite.search[dev]'
$ .venv/bin/pip install --editable 'src/edrn.theme[dev]'
$ .venv/bin/pip install --editable 'src/edrnsite.ploneimport[dev]'
$ .venv/bin/pip install --editable 'src/edrnsite.policy[dev]'
$ .venv/bin/pip install --editable 'src/edrnsite.test[dev]'
$ .venv/bin/django-admin migrate --pythonpath . --settings local
$ .venv/bin/django-admin createsuperuser --pythonpath . --settings local --username root --email edrn-ic@jpl.nasa.gov
```

When prompted for a password, enter a suitably secure root-level password for the Django super user (twice).

**👉 Note:** This password is for the application server's "manager" or "root" superuser and is unrelated to any usernames or passwords used with the EDRN Directory Service. But because it affords such deep and penetrative access, it must be kept double-plus super-secret probationary secure.

Then, to run a local server so you can point your browser at http://localhost:8000/ simply do:

```console
$ .venv/bin/django-admin runserver --pythonpath . --settings local
```

You can also visit the Wagtail admin at http://localhost:8000/admin/ and the Django admin at http://localhost:8000/django-admin/

To see all the commands besides `runserver` and `migrate` that Django supports:

```console
$ .venv/bin/django-admin help --pythonpath . --settings local
```


### 🍃 Environment Variables

Here is a table of the environment variables that may affect the portal server (some of these have explicit values depending on context, such as containerization):

| Variable                | Use                                                             | Default |
|-------------------------|-----------------------------------------------------------------|---------|
| `ALLOWED_HOSTS`         | What valid hostnames to serve the site on (comma-separated)     | `.nci.nih.gov,.cancer.gov` |
| `AWS_ACCESS_KEY_ID`     | Amazon Location Service account access key                      | Unset |
| `AWS_SECRET_ACCESS_KEY` | Amazon Location Service secret access key                       | Unset |
| `BASE_URL`              | Full URL base for generating URLs in notification emails        | `https://edrn.nci.nih.gov/` |
| `CACHE_URL`             | URL to the caching & message brokering service                  | `redis://` |
| `CSRF_TRUSTED_ORIGINS`  | Comma-separated list of origins we implicity trust in form req  | `http://*.nci.nih.gov,https://*.nci.nih.gov` |
| `DATABASE_URL`          | URL to persistence                                              | Unset |
| `ELASTICSEARCH_URL`     | Where the search engine's ReST API is                           | `http://localhost:9200/` |
| `FORCE_SCRIPT_NAME`     | Base URI path (Apache "script name") if app is not on `/`       | Unset |
| `LDAP_BIND_DN`          | Distinguished name to use for looking up users in the directory | `uid=service, dc=edrn, dc=jpl, dc=nasa, dc=gov` |
| `LDAP_BIND_PASSWORD`    | Password for the `LDAP_BIND_DN`                                 | Unset |
| `LDAP_CACHE_TIMEOUT`    | How many seconds to cache directory lookups                     | `3600` seconds (1 hour) |
| `LDAP_URI`              | URI to locate the EDRN Directory Service                        | `ldaps://edrn-ds.jpl.nasa.gov` |
| `MEDIA_ROOT`            | Where to save media files                                       | Current dir + `/media` |
| `MEDIA_URL`             | URL prefix of media files; must end with `/`                    | `/media/` |
| `MQ_URL`                | URL to the message queuing service                              | `redis://` |
| `RECAPTCHA_PRIVATE_KEY` | Private key for reCAPTCHA                                       | Unset |
| `RECAPTCHA_PUBLIC_KEY`  | Public key for ereCAPTCHA                                       | Unset | 
| `SECURE_COOKIES`        | `True` for secure handling of session and CSRF cookies          | `True` |
| `SIGNING_KEY`           | Cryptographic key to protect sessions, messages, tokens, etc.   | Unset in operations; set to a known _bad_ value in development |
| `STATIC_ROOT`           | Where to collect static files                                   | Current dir + `/static` |
| `STATIC_URL`            | URL prefix of static files; must end with `/`                   | `/static/` |

Note that the `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` can be set through-the-web; the environment variables are just a fallback. Sadly, neither `RECAPTCHA_PRIVATE_KEY` nor `RECAPTCHA_PUBLIC_KEY` can due to limitations of [wagtail-django-recaptcha](https://github.com/springload/wagtail-django-recaptcha).


## 🪶 Apache HTTPD Configuration with Jenkins

This section describes how you'd use Apache HTTPD with Jenkins in order to make the site accessible to the world.

First up, the HTTPD configuration:

```
WSGIDaemonProcess edrnportal user=edrn group=edrn python-home=/usr/local/edrn/portal/p5-renaissance/venv 
WSGIProcessGroup edrnportal
WSGIScriptAlias /portal/renaissance /usr/local/edrn/portal/p5-renaissance/jenkins.wsgi process-group=edrnportal
Alias /portal/renaissance/media/ /usr/local/edrn/portal/p5-renaissance/media/
Alias /portal/renaissance/static/ /usr/local/edrn/portal/p5-renaissance/static/
<Directory "/usr/local/edrn/portal/p5-renaissance">
    <IfVersion < 2.4>
        Order allow,deny
        Allow from all
    </IfVersion>
    <IfVersion >= 2.4>
        Require all granted
    </IfVersion>
</Directory>
<Directory "/usr/local/edrn/portal/p5-renaissance/static/">
    Options FollowSymLinks
</Directory>
```
Next, here's the `jenkins.wsgi` that was referenced in the HTTPD configuration above (Jenkins should generate this with each build):
```python
from django.core.wsgi import get_wsgi_application
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edrnsite.policy.settings.ops')
os.environ.setdefault('LDAP_BIND_DN', 'uid=service,dc=edrn,dc=jpl,dc=nasa,dc=gov')
os.environ.setdefault('LDAP_BIND_PASSWORD', 'REDACTED')
os.environ.setdefault('SIGNING_KEY', 'REDACTED')
os.environ.setdefault('DATABASE_URL', 'postgresql://:@/edrn')
os.environ.setdefault('ALLOWED_HOSTS', '.jpl.nasa.gov')
os.environ.setdefault('STATIC_ROOT', '/usr/local/edrn/portal/p5-renaissance/static')
os.environ.setdefault('MEDIA_ROOT', '/usr/local/edrn/portal/p5-renaissance/media')
os.environ.setdefault('BASE_URL', 'https://edrn-dev.jpl.nasa.gov/portal/renaissance/')
os.environ.setdefault('STATIC_URL', '/portal/renaissance/static/')
os.environ.setdefault('MEDIA_URL', '/portal/renaissance/media/')
os.environ.setdefault('SECURE_COOKIES', 'False')
os.environ.setdefault('ELASTICSEARCH_URL', 'http://localhost:9200/')
os.environ.setdefault('CACHE_URL', 'redis://')
# We don't need FORCE_SCRIPT_NAME here since Apache's WSGISCriptAlias does the right thing
application = get_wsgi_application()
```
Finally, this needs to be run on each deployment:
```console
$ venv/bin/django-admin collectstatic --settings erdnsite.policy.settings.ops --clear --link
$ mkdir media
```


## 🚢 Container Setup

To use this software in a [Docker](https://docker.com/) container environment, first collect the wheels by running:

    support/build-wheels.sh

Or by hand:

    .venv/bin/python -m build --outdir dist src/eke.geocoding
    .venv/bin/python -m build --outdir dist src/edrnsite.streams
    .venv/bin/python -m build --outdir dist src/edrnsite.controls
    .venv/bin/python -m build --outdir dist src/edrnsite.content
    .venv/bin/python -m build --outdir dist src/edrn.collabgroups
    .venv/bin/python -m build --outdir dist src/edrn.auth
    .venv/bin/python -m build --outdir dist src/edrn.theme
    .venv/bin/python -m build --outdir dist src/edrnsite.search
    .venv/bin/python -m build --outdir dist src/eke.knowledge
    .venv/bin/python -m build --outdir dist src/eke.biomarkers
    .venv/bin/python -m build --outdir dist src/edrnsite.ploneimport
    .venv/bin/python -m build --outdir dist src/edrnsite.policy

You don't need `src/edrnsite.test` since it's just used for testing.

Repeat this for any other source directory in `src`. Then build the image:

    docker image build --build-arg user_id=NUMBER --tag edrn-portal:latest --file docker/Dockerfile .

Replace `NUMBER` with the number of the user ID of the user under which to run the software in the container. Typically you'll want

-   500 for running at the Jet Propulsion Laboratory.
-   26013 for running at the National Cancer Institute.

Spot check: see if the image is working by running:

    docker container run --rm --env LDAP_BIND_PASSWORD='[REDACTED]' --env SIGNING_KEY='s3cr3t' \
        --env ALLOWED_HOSTS='*' --publish 8000:8000 edrn-portal:latest

and visit http://localhost:8000/ and you should get `Sever Error (500)` since the database connection isn't established.

For a Docker Composition, the accompanying `docker/docker-compose.yaml` file enables you to run the orchestrated set of needed processes in production, including the portal, maintenance worker, search engine, cache and message queue, and a database. You can launch all the processes at once with `docker compose up`.

**👉 Note:** On some systems, `docker compose` is actually `docker-compose`.

The [environment variables listed above](#user-content-environment-variables) also apply to the `docker compose` command. The defaults in `docker/docker-compose.yaml` are suitable for running at the National Cancer Institute, but the environment variables absolutely need to be adjusted for _every_ other context. A table of the additional environment variables follows:

| Variable              | Use                                                              | Default               |
|-----------------------|------------------------------------------------------------------|-----------------------|
| `EDRN_DATA_DIR`       | Volume to bind to provide media files and PostgreSQL DB          | `/local/content/edrn` |
| `EDRN_IMAGE_OWNER`    | Name of image owning org.; use an empty string for a local image | `edrndocker/`         |
| `EDRN_PUBLISHED_PORT` | TCP port on which to make the HTTP service available             | 8080                  |
| `EDRN_TLS_PORT`       | Encrypted TCP port, if the `tls-proxy` profile is enabled        | 4134                  |
| `EDRN_VERSION`        | Version of the image to use, such as `latest`                    | `6.0.0`               |
| `POSTGRES_PASSWORD`   | Root-level password to the PostgreSQL database server            | Unset                 |

These variables are also necessary while setting up the containerized database.

Ater setting the needed variables, start the composition as follows:

    docker compose --project-name edrn --file docker/docker-compose.yaml up --detach

You can now proceed to set up the database, search engine, and populate the portal with its content.


### 📀 Containerized Database Setup

Next, we need to set up the database with initial structure and content. This section tells you how.


#### 🏛 Database Structure

To set up the initial database and its schema inside a Docker Composition, we start by creating the database:

    docker compose --project-name edrn --file docker/docker-compose.yaml \
        exec db createdb --username=postgres --encoding=UTF8 --owner=postgres edrn

**👉 Note:** You must set the same environment variables in the above command—and the subsequent commands—as running the entire composition—especially the `POSTGRES_PASSWORD`.

Next, run the Django database migrations (again, with the environment set):

    docker compose --project-name edrn --file docker/docker-compose.yaml \
        exec portal django-admin makemigrations
    docker compose --project-name edrn --file docker/docker-compose.yaml \
        exec portal django-admin migrate


#### 👴 Import Content from Plone

👉 **Note:** This is no longer necessary. Plone hasn't been used in a while now; instead you just upgrade from the previous Wagtail-based version. However, I'm leaving this information intact for posterity and reference. Skip down to "Populate the Rest of the Content".

The next step is to bring the content from the older Plone-based site into the new Wagtailb-ased site. You will need the following:

-   `edrn.json`, a file containing the hierarchical content; ask the portal developer for a copy.
-   `export_defaultpages.json`, a file indicating the view for "folderish" content types; ask the portal developer for a copy.
-   The Plone URL prefix used to construct the `edrn.json` file; ask the developer for the correct value.
-   The `blobstorage` directory used by Plone; this is available on the host running the Plone version of the portal.

Import the content from the old Plone site (with the environment variables from above still set):

    docker compose --project-name edrn --file docker/docker-compose.yaml \
        run --volume PLONE_EXPORTS_DIR:/mnt/zope --volume PLONE_BLOBS:/mnt/blobs \
        --entrypoint /usr/bin/django-admin --no-deps portal importfromplone \
        PLONE_URL /mnt/zope/edrn.json /mnt/zope/export_defaultpages.json /mnt/blobs

Subsituting:

-   `PLONE_EXPORTS_DIR` with the path to the directory containing the `edrn.json` and `export_defaultpages.json` files (sold separately)
-   `PLONE_BLOBS` with the path to the Zope `blobstorage` directory, such as `/local/content/edrn/blobstorage`
-   `PLONE_URL` with the prefix URL (provided by the portal developer)

For example, you might save `edrn.json` and `export_defaultpages.json` to `/tmp`, have your blobs in `/local/content/edrn/blobstorage`, and be told that the prefix URL is `http://nohost/edrn/`; in that case, you'd run:

    docker compose --project-name edrn --file docker/docker-compose.yaml \
        run --volume /tmp:/mnt/zope --volume /local/content/edrn/blobstorage:/mnt/blobs \
        --entrypoint /usr/bin/django-admin --no-deps portal importfromplone \
        http://nohost/edrn/ /mnt/zope/edrn.json /mnt/zope/export_defaultpages.json /mnt/blobs


#### 🥤 Populate the Rest of the Content

You can then populate the rest of the database with EDRN content, maps, menus, and so forth (with the environment still set) by running:

    docker compose --project-name edrn --file docker/docker-compose.yaml \
        exec portal django-admin collectstatic --no-input

This step is no longer necessary; it was used only for the first instance of the Wagtail-based site. I'm leaving it here for future reference. Don't try to run it; it won't work.

    env AWS_ACCESS_KEY_ID=KEY AWS_SECRET_ACCESS_KEY=SECRET docker compose --project-name edrn \
        --file docker/docker-compose.yaml \
        exec portal django-admin edrnbloom --hostname HOSTNAME

Instead, skip down to this next step:

    docker compose --project-name edrn --file docker/docker-compose.yaml \
        exec portal django-admin ldap_group_sync
    docker compose --project-name edrn --file docker/docker-compose.yaml \
        exec portal django-admin rdfingest  # This can take a long time, 10–20 minutes
    docker compose --project-name edrn --file docker/docker-compose.yaml \
        exec portal django-admin autopopulate_main_menus

In the above, replace `HOSTNAME` with the host name of the portal, such as `edrn-dev.nci.nih.gov` or `edrn-stage.nci.nih.gov` or even `edrn.nci.nih.gov`. Replace `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` with their corresponding values. If you don't know them, leave them unset.

Lastly, stop the entire service and remove the orphaned containers made during the above steps:

    docker compose --project-name edrn --file docker/docker-compose.yaml \
        down --remove-orphans

Then, start it up again, officially!

    docker compose --project-name edrn --file docker/docker-compose.yaml \
        up --detach

Then you can point a browser at http://localhost:4135/ (or whatever the `EDRN_PUBLISHED_PORT` is) and see if it worked. Note that things won't look quite right because static resources aren't loaded on this endpoint URL. The front-end application load balancer or reverse-proxy must serve those.


### 🕸 Reverse Proxy: ELB, ALB, Nginx, Apache HTTPD, etc.

The Docker Composition itself is not enough, of course. The last step is to set up an actual _web server_ to accept requests, serve static and media files, reverse-proxy to the portal container, handle TLS/SSL encryption, load balancing, and so forth.

The web server is also responsible for serving media files and static assets. This is for efficiency: there's no need to involve the backend content management system for such files (which can be large). Furthermore, by giving the server direct filesystem access, it can use the `sendfile` system call, which is blazingly efficient.

In a nutshell, the web server must serve MEDIA_URL requests to the MEDIA_ROOT directory (which is EDRN_DATA_DIR/media), STATIC_URL requests to the STATIC_ROOT directory (which is EDRN_DATA_DIR/static), and all other requests reverse-proxied to the EDRN_PUBLISHED_PORT (or EDRN_TLS_PORT if you're using it) TCP socket.

How you configure an Elastic Load Balancer, Application Load Balancer, Nginx, Apache HTTPD, or other web server to handle reverse-proxying to the portal container as well as serving static and medial files depends on the software in use. In the interests of including a working example, though, see the following Nginx configuration:
```nginx
server {
    listen …;
    location /media/ {                 # Request = http://whatever/media/documents/sentinel.dat
        root /local/web/content/edrn;  # Response = /local/web/content/edrn/media/documents/sentinel.dat
    }
    location /static/ {                # Request = http://whatever/static/edrn.theme/css/edrn-overlay.css
        root /local/web/content/edrn;  # Response = /local/web/content/edrn/static/edrn.theme/css/edrn-overlay.css
    }
    location / {                           # All other requests go to the portal container
        proxy_pass http://localhost:4135;  # EDRN_PUBLISHED_PORT = 4135
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect default;        
    }
}
```


#### 🔻 Subpath Serving

Normally, the EDRN portal is hosted on the root path `/` of a host; for example, in production it's at `https://edrn.nci.nih.gov/`. However, for certain demonstrations and other expositions, it may be necessary to host it on a "subpath", such as `https://edrn.jpl.nasa.gov/portal/renaissance/`. Here, the subpath is `/portal/renaissance/`.

Depending on the web server, you may not need to do anything to support such a configuration, because the web server recognizes the subpath and sets the `SCRIPT_NAME` environment variable to the subpath (this is the case for mod_wsgi). Others, such as reverse-proxies, make no assumptions and make no such setting. When this is the case, you can set the `FORCE_SCRIPT_NAME` environment variable in the Docker composition to force the portal to believe a `SCRIPT_NAME` was set even when it wasn't.

As an example, if the web server is reverse-proxying to the Docker composition for URLs such as `https://edrn.jpl.nasa.gov/portal/renaissance/`, then we'd set `FORCE_SCRIPT_NAME` when starting the composition to `/portal/renaissance/`.


## 👩‍💻 Software Environment

To develop for this system, you'll need 

-   PostgreSQL 13 or later, but not 15 or later
-   Python 3.9 or later, but not 4.0 or later
-   Elasticsearch 7.17 or later, but not 8.0 or later
-   Redis 7.0 or later, but not 8.0 or later
   

### 👥 Contributing

You can start by looking at the [open issues](https://github.com/EDRN/P5/issues), forking the project, and submitting a pull request. You can also [contact us by email](mailto:ic-portal@jpl.nasa.gov) with suggestions.


### 🔢 Versioning

We use the [SemVer](https://semver.org/) philosophy for versioning this software. For versions available, see the [releases made](https://github.com/EDRN/P5/releases) on this project. We're starting off with version 5 because reasons.


## 👩‍🎨 Creators

The principal developer is:

- [Sean Kelly](https://github.com/nutjob4life)

The QA team consists of:

- [Heather Kincaid](https://github.com/hoodriverheather)
- [Maureen Colbert](https://github.com/colbertm)

To contact the team as a whole, [email the Informatics Center](mailto:ic-portal@jpl.nasa.gov).


## 📃 License

The project is licensed under the [Apache version 2](LICENSE.md) license.
