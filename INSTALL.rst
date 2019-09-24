**************
 Installation
**************


Notes
=====

Experimentation::

For commands below (csh style) and for ``docker-compose.yml``::

    setenv EDRN_PORTAL_VERSION 5.0.0
    setenv EDRN_DATA_DIR ${HOME}/Downloads/docker-data/edrn
    setenv EDRN_PUBLISHED_PORT 2345
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


Docker Composition
------------------

Start (including perhaps build, don't forget env vars)::

    docker-compose up

You could also put in ``--detach``.

To debug::

    docker-compose exec edrn-portal /bin/bash
