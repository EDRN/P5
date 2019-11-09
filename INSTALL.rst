**************
 Installation
**************


Notes
=====

Experimentation::

For commands below (csh style) and for ``docker-compose.yml``::

    setenv EDRN_PORTAL_VERSION 5.0.0
    setenv EDRN_DATA_DIR ${HOME}/Downloads/docker-data/edrn
    setenv EDRN_PUBLISHED_PORT 4135
    mkdir -p ${EDRN_DATA_DIR}


Dockerfile
----------

To explore a plain Plone container::

    docker run \
        --interactive --tty \
        --publish ${EDRN_PUBLISHED_PORT}:8080 \
        --volume /tmp/plain-plone/filestorage:/data/filestorage \
        --volume /tmp/plain-plone/blobstorage:/data/blobstorage \
        --volume /tmp/plain-plone/log:/data/log \
        --entrypoint /bin/bash \
        plone:5.1.5

To build::
        
    docker build --tag edrn-p5 .


Running Standalone
~~~~~~~~~~~~~~~~~~

Explore::

    docker run \
        --interactive --tty \
        --publish ${EDRN_PUBLISHED_PORT}:8080 \
        --volume ${EDRN_DATA_DIR}/filestorage:/data/filestorage \
        --volume ${EDRN_DATA_DIR}/blobstorage:/data/blobstorage \
        --volume ${EDRN_DATA_DIR}/log:/data/log \
        --entrypoint /bin/bash \
        edrn-p5:latest
        
Run::

    docker run \
        --publish ${EDRN_PUBLISHED_PORT}:8080 \
        --volume ${EDRN_DATA_DIR}/filestorage:/data/filestorage \
        --volume ${EDRN_DATA_DIR}/blobstorage:/data/blobstorage \
        --volume ${EDRN_DATA_DIR}/log:/data/log \
        edrn-p5:latest

You could add ``--detach`` too.


With ZEO Database Server
~~~~~~~~~~~~~~~~~~~~~~~~

First create a network::

    docker network create --driver bridge --label 'org.label-schema.name=EDRN P5 Network' edrn-network

Start ZEO::

    docker run \
        --detach \
        --name edrn-zeo \
        --network edrn-network \
        --volume ${EDRN_DATA_DIR}/filestorage:/data/filestorage \
        --volume ${EDRN_DATA_DIR}/blobstorage:/data/blobstorage \
        --volume ${EDRN_DATA_DIR}/log:/data/log \
        edrn-p5:latest \
        zeo

Then start an instance::

    docker run \
        --name edrn-zope \
        --network edrn-network \
        --env ZEO_ADDRESS=edrn-zeo:8080 \
        --env ZEO_SHARED_BLOB_DIR=on \
        --publish ${EDRN_PUBLISHED_PORT}:8080 \
        --volume ${EDRN_DATA_DIR}/blobstorage:/data/blobstorage \
        --volume ${EDRN_DATA_DIR}/log:/data/log \
        edrn-p5:latest

You could add ``--detach`` too.

NOTE: you must do::

    curl http://localhost:${EDRN_PUBLISHED_PORT}/edrn/publications

as the first request or the plone.subrequest VHM gets screwed up! NO IDEA WHY!

To change the Zope password with a running ZEO and instance::

    docker run \
        --rm \
        --interactive \
        --tty \
        --network edrn-network \
        --env ZEO_ADDRESS=edrn-zeo:8080 \
        edrn-p5:latest \
        adduser NEWUSER PASSWORD

Replace NEWUSER and PASSWORD with desired values. (Yes, this puts the PASSWORD
in the process list; do so from a secure place.)


Docker Composition
------------------

Start (including perhaps build, don't forget env vars)::

    docker-compose --project-name edrn up --detach

NOTE: you must do::

    curl http://localhost:${EDRN_PUBLISHED_PORT}/edrn/publications

as the first request or the plone.subrequest VHM gets screwed up! NO IDEA WHY!

To change the Zope password::

    docker run \
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
