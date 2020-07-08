*******
 Notes
*******

These are notes primarily by Sean_ that should probaby become proper
documentation some day, possibly in the wiki_ or as part of the ``docs`` dir.


Docker
======

Once you consider putting together chroot jails, layered filesystems, and IP
tables tricks, "containers" aren't that mysterious after all.  Docker_ is the
one to use, apparently.

For commands below (csh style) and for ``docker-compose.yaml``, first set some
environment variables::

    setenv EDRN_PORTAL_VERSION 5.0.2
    setenv EDRN_DATA_DIR ${HOME}/Downloads/docker-data/edrn
    setenv EDRN_PUBLISHED_PORT 4135
    mkdir -p ${EDRN_DATA_DIR}/log

..  Note:: On some JPL systems, the Docker daemon and ``docker`` command-line
    client versions are newer than the ``docker-compose`` version.  As a
    result, some features used in the ``docker-compose.yaml`` file—like
    interpolating values from environment variables—may not work.  Be prepared
    to hand-edit files.

    This may be the case on *other* systems too.

    At least Docker Desktop (2.3.0.3) for macOS gets it right:

    • Engine = 19.03.8
    • Compose = 1.25.5
    • Kubernetes = v1.16.5
    • Notary = 0.6.1
    • Credential Helper = 0.6.3


Using the Dockerfile
--------------------

To build the EDRN P5 image for the free world::
        
    docker image build --tag edrn-p5 .

But for NCI it's::

    docker image build --tag edrn-p5 --file Dockerfile-nci .

Then you can publish it::

    docker login
    docker image tag edrn-p5:latest nutjob4life/edrn-p5:latest
    docker image push nutjob4life/edrn-p5:latest

By the way, if you need to explore a plain Plone container::

    docker container run \
        --interactive \
        --tty \
        --publish ${EDRN_PUBLISHED_PORT}:8080 \
        --volume /tmp/plain-plone/filestorage:/data/filestorage \
        --volume /tmp/plain-plone/blobstorage:/data/blobstorage \
        --volume /tmp/plain-plone/log:/data/log \
        --entrypoint /bin/bash \
        plone:5.1.5


..  Note:: I prefer to use ``docker container run`` instead of ``docker run``,
    ``docker container ls`` instead of ``docker ps``, ``docker image build``
    instead of ``docker build``, etc., in order to underscore the differences
    between the objects that Docker managed (containers, images, etc.).
    Comprehending these differences helps my productivity.


Using Docker Directly
---------------------

There are several ways to use Docker; again, think abstractions on
abstractions: a container is just a chroot+layered filesystem+ip tables
tricks. Instead of managing those three things separately, at the ``docker``
daemon level we manage them in concert: we're manipulating the "low level"
objects in *that* space: containers (running instances), the images they're
built from, and their resources (like volumes that appear in their layered
filesystems, networks they communciate with, etc.). And there's a layer
*above* that: at the ``docker-compose`` level, we treat the volumes, networks,
and services (containers and their support environment) as a whole as the
units of management.

It's helpful to understand the lower levels (``docker``) and then graduate to
the higher (``docker-compose``) levels.  So let's do that.

To explore::

    docker container run \
        --interactive \
        --tty \
        --publish ${EDRN_PUBLISHED_PORT}:8080 \
        --volume ${EDRN_DATA_DIR}/filestorage:/data/filestorage \
        --volume ${EDRN_DATA_DIR}/blobstorage:/data/blobstorage \
        --volume ${EDRN_DATA_DIR}/log:/data/log \
        --entrypoint /bin/bash \
        edrn-p5:latest

To run::

    docker container run \
        --publish ${EDRN_PUBLISHED_PORT}:8080 \
        --volume ${EDRN_DATA_DIR}/filestorage:/data/filestorage \
        --volume ${EDRN_DATA_DIR}/blobstorage:/data/blobstorage \
        --volume ${EDRN_DATA_DIR}/log:/data/log \
        edrn-p5:latest

You could add ``--detach`` too.


..  Important:: You **must** do:: 

        curl http://localhost:${EDRN_PUBLISHED_PORT}/edrn/publications

    as the first request or the plone.subrequest VHM gets screwed up! NO IDEA WHY!


With ZEO Database Server
~~~~~~~~~~~~~~~~~~~~~~~~

Again, you'd do this at the Docker Composition level, but let's try it "by
hand".  first create a network::

    docker network create --driver bridge --label 'org.label-schema.name=EDRN P5 Network' edrn-network

Start ZEO::

    docker container run \
        --detach \
        --name edrn-zeo \
        --network edrn-network \
        --volume ${EDRN_DATA_DIR}/filestorage:/data/filestorage \
        --volume ${EDRN_DATA_DIR}/blobstorage:/data/blobstorage \
        --volume ${EDRN_DATA_DIR}/log:/data/log \
        edrn-p5:latest \
        zeo

Then start an instance::

    docker container run \
        --name edrn-zope \
        --network edrn-network \
        --env ZEO_ADDRESS=edrn-zeo:8080 \
        --env ZEO_SHARED_BLOB_DIR=on \
        --publish ${EDRN_PUBLISHED_PORT}:8080 \
        --volume ${EDRN_DATA_DIR}/blobstorage:/data/blobstorage \
        --volume ${EDRN_DATA_DIR}/log:/data/log \
        edrn-p5:latest

You could add ``--detach`` too.

..  Important:: You **must** do:: 

        curl http://localhost:${EDRN_PUBLISHED_PORT}/edrn/publications

    as the first request or the plone.subrequest VHM gets screwed up! NO IDEA WHY!


Zope Manager Password
~~~~~~~~~~~~~~~~~~~~~

You have to use ZEO and a separate instance to change the Zope manager
password.  To do so, create a network and start ZEO as above, then::

    docker container run \
        --rm \
        --interactive \
        --tty \
        --network edrn-network \
        --env ZEO_ADDRESS=edrn-zeo:8080 \
        edrn-p5:latest \
        adduser NEWUSER PASSWORD

Replace NEWUSER and PASSWORD with desired values. (Yes, this puts the PASSWORD
in the process list; do so from a secure place.)


Using a Docker Composition
--------------------------

This is how you'll really want to do things, whether you're in operations,
demonstration, testing, or even on your personal Docker Community Edition
MacBook Pro in your casual development lab.

Note that the ``docker-compose.yaml`` file uses the image
``nutjob4life/edrn-p5``.  Make sure you've built and published one.  You might
quickly edit the file and just use your local ``edrn-p5`` image.

To start it::

    mkdir -p ${EDRN_DATA_DIR}/log
    docker-compose --project-name edrn up --detach

If your ``docker-compose`` doesn't recognize ``--detach``, try ``-d``.

..  Important:: You **must** do::

        curl http://localhost:${EDRN_PUBLISHED_PORT}/edrn/

    as the first request or the plone.subrequest VHM gets screwed up! NO IDEA WHY!

To change the Zope password::

    docker container run \
        --rm \
        --network edrn_backplane \
        --env ZEO_ADDRESS=edrn-db:8080 \
        edrn-p5:latest \
        adduser NEWUSER PASSWORD

Note if you used a different ``--project-name`` in the ``docker-compose``, use
it as a prefix to ``--network`` in place of ``edrn``.  Replace NEWUSER and
PASSWORD with desired values. (Yes, this puts the PASSWORD in the process
list; do so from a secure place.)

To debug (i.e., start a shell in the ``edrn-portal`` service)::

    docker-compose --project-name edrn exec edrn-portal /bin/bash


RDF for LabCAS
==============

With David's code: https://edrn-dev.jpl.nasa.gov/cancerdataexpo/rdf-data/edrnlabcas/@@rdf
A static extract: https://mcl.jpl.nasa.gov/ksdb/static/tmp/labcas.txt

The "static extract" was mentioned on https://mcl.jpl.nasa.gov/ksdb/static/tmp/labcas.txt


Apache HTTPD
============

Here's a sample Apache HTTPD stanza::

    <VirtualHost *:443>
        ServerName edrn.nci.nih.gov
        ServerAlias edrn
        ServerAdmin nciappsupport@nih.gov
        DocumentRoot /var/www/html
        ErrorLog "/var/log/httpd/edrn_error.log"
        CustomLog "/var/log/httpd/edrn_access.log" combined 
        SSLEngine on
        SSLCertificateFile "/etc/pki/tls/certs/edrn.crt"
        SSLCertificateKeyFile "/etc/pki/tls/private/edrn.key"
        SSLCertificateChainFile "/etc/pki/tls/certs/DigiCertCA.crt"
        RewriteEngine on
        RewriteRule ^/(.*) http://DOCKERHOST:DOCKERPORT/VirtualHostBase/https/edrn.nci.nih.gov:443/edrn/VirtualHostRoot/$1 [L,P]
    </VirtualHost>

The ``RewriteRule`` does it all: it reverse-proxies (the ``[P]`` flag) to
whatever the ``DOCKERHOST`` is, to the app listening on published
``DOCKERPORT`` ($EDRN_PUBLISHED_PORT set way above at the top of this
document, probably). At this point, the container running Zope+Plone+EDRN
Portal gets to see ``/VirtualHostBase`` which tells it "hey, big old virtual
host monster URL coming up". The next component says "OK, when I generate URLs
in my response documents, use ``https`` as the scheme. Then, "when I generate
URLs, use ``edrn.nci.nih.gov`` as the hostname and ``443`` as the port". At
this point, it finds the ``edrn`` object in the Zope database and lets that
PloneSite object handle the request, because ``VirtualHostRoot`` says we're
done traversing the Zope database.  Finally, the rest of the URL (``$1``) gets
handled by Plone and the EDRN site.  The ``[L]`` flag says to Apache "this is
the last RewriteRule; we're done here".


Python Setup
============

When attempting to build this site (or any of its components under ``src``),
use Python 2.7 with the following packages pre-installed::

• ``setuptools==38.5.1``
• ``pip==18.1``
• ``wheel-0.32.2``


Notes
-----

``p5pyp2.7`` aliased to ``~/Documents/Development/python2.7/bin/python2.7``
which is the Python environment as described above.

To build::

    p5py2.7 bootstrap.py -c dev.cfg
    bin/buildout -c dev.cfg
    bin/zope-debug run support/admin.py root root
    bin/zope-debug run support/createEDRNSite.py root root
    bin/zope-debug run support/ldap-password.py 'LDAP-PASSWORD-HERE'
    env ZEXP_EXPORTS=/path/to/zexp-exports-dir bin/zope-debug run support/loadZEXPFiles.py root root
    bin/zope-debug fg
    curl http://localhost:6468/edrn



.. References:
.. _Sean: https://github.com/nutjob4life
.. _wiki: https://github.com/EDRN/P5/wiki
.. _Docker: https://www.docker.com