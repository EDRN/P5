**************
 Installation
**************

To run the Early Detection Research Network's (EDRN's) Public Portal and
Knowledge Environment (nicknamed P5), you'll need the following:

• A Docker environment
• The EDRN P5 image, ``nutjob4life/edrn-p5``
• An EDRN content database
• The Docker Composition ``docker-compose.yaml`` file
• A public web server (such as Apache HTTPD, NGINX, AWS Elastic Load Balancer,
  etc.)


🏃‍♀️ Quick Start
=================

To get up and running quickly with the "lite" content database, try this::

    export EDRN_PORTAL_VERSION=5.0.0
    export EDRN_PUBLISHED_PORT=4135
    export EDRN_DATA_DIR=${HOME}/docker-data/edrn
    mkdir -p $EDRN_DATA_DIR/log
    curl -L https://github.com/EDRN/P5/releases/download/5.0.0/edrn-lite.tbz | \
        tar --directory ${HOME}/docker-data --extract --bzip2
    curl -LO https://github.com/EDRN/P5/releases/download/0.0.0/docker-compose.yaml
    docker-compose --project-name edrn up --detach
    curl http://localhost:${EDRN_PUBLISHED_PORT}/edrn/ && echo OK
    # Now to set up my reverse proxy, ELB, whatever!

Need details? The full content database? Help? Keep reading!


🌳 Docker Environment
======================

The EDRN P5 works with Docker 19.03.5 and Docker Compose 1.24.1. You'll also
need a filesystem to unpack and hold the EDRN content database (at least 8
gigabytes to start, double that for future growth).

You'll also need to set these environment variables:

•  ``EDRN_PORTAL_VERSION=5.0.0``. Replace 5.0.0 with whatever version of the
   software you're using; as of this writing (December 2019) 5.0.0 is the
   current release.
•  ``EDRN_PUBLISHED_PORT=4135``. Replace 4135 with whatever port you like or
   leave it as is.
•  ``EDRN_DATA_DIR=${HOME}/docker-data/edrn``. Replace this with wherever you
   unpacked the EDRN content database; the content database should be an
   ``edrn`` directory with ``blobstorage``, ``filestorage``, and ``log``
   subdirectories; see "EDRN Content Database" below.

..  Important:: You may need to create ``${EDRN_DATA_DIR}/log`` if it
    doesn't come unpacked from the EDRN Content Database (below).


📚 EDRN Content Database
=========================

The EDRN content database contains the Zope database and support BLOB files
that contains the web pages, stylesheets, etc., for the EDRN site. Two
versions are available:

• **Lite**. The lite database is about 33 megabytes in size and is suitable to
  ensure things are working, as well as for testing the software with tools
  like IBM Rational App Scan. You can get this database from GitHub_ by
  navigating to "Releases" and look under the "Assets" for the latest release.
  The file is ``edrn-lite.tbz``.
• **Full**. The full database is 7.3 gigabytes in size and contains all of the
  production content for EDRN, including proprietary data specifically for
  EDRN researchers and available only with a login. You can get this database
  by request by the portal developer_ at the EDRN Informatics Center. **Do
  not distribute this database**. The file is ``edrn.tbz``.

Regardless of which database you use, unpack it with ``tar --extract --bzip2``
and ensure the ``$EDRN_DATA_DIR`` environment variable points to the extracted
``edrn`` directory.  As mentioned in the "Important" note above, ensure a
``${EDRN_DATA_DIR}/log`` directory also exists; create it with ``mkdir`` if
necessary. You should have::

    📁 edrn ($EDRN_DATA_DIR)
        📁 blobstorage
            📄 .layout
            📁 0x00
            📁 tmp
            …
        📁 filestorage
            📄 Data.fs
            📄 Data.fs.index
            …
        📁log


📓 Docker Composition
======================

The P5 site uses three Docker services to run:

• **Zope application server**. This runs the Plone content management system
  and the custom EDRN software.
• **Zope Enterprise Objects (ZEO)**. This is the database server used by Zope.
• **Memcached**. This is a in-memory cache that optimizes serving parts of the
  site.

These three services communicate using their own internal dOcker network.

Now that you know all this, *forget it!* The ``docker-compose.yaml`` file sets
all this up for you. You can get the ``docker-compose.yaml`` file from the
same place as the EDRN Content Database: on GitHub_, under "Releases", and
under "Assets" for the latest release.

To start things up, then, you just need the environment variables and
extracted content database (above), and the ``docker-compose.yaml`` file
in the current directory, and run::

    docker-compose --project-name edrn up --detach

You can see the log output by running::

    docker-compose --project-name edrn logs --follow

Note that *you must absolutely make an HTTP request to the site now* before
setting up a reverse proxy (next section, below) in order to set some initial
values in the database. Run::

    curl http://localhost:${EDRN_PUBLISHED_PORT}/edrn/

and if you're using the *full* database, *also do*::

    curl http://localhost:${EDRN_PUBLISHED_PORT}/edrn/publications

This also is a good test to see if things are working; you should get HTML
responses.

To stop the site, run::

    docker-compose --project-name edrn down


💁‍♀️ Public Web Server (Reverse Proxy)
=======================================

The final step is then to make the service available to the public internet.
You typically do this by running a separate web server, load balancer,
Elastic Load Balancer, etc., that reverse-proxies to the Docker Composition
(running from above). We'll assume that the public site will be available
by ``https`` (and that ``http`` requests get redirected to ``https``).
Configuring your web server/ELB/whatever for SSL/TLS is up to you.

So that the P5 site can create HTML documents with the correct external URLs,
you just need to set up your public server to reverse-proxy all requests to
your Docker host's $EDRN_PUBLISHED_PORT TCP/IP port with a special rewritten
URI prefix. The proxied URI should consist of the following:

• The string ``/VirtualHostBase/https``
• The public host name of the site, such as ``edrn.nci.nih.gov``
• The string ``:443/edrn/VirtualHostRoot/``
• The incoming URI

For example, someone using a browser to visit the page::

    https://edrn.nci.nih.gov/biomarkers/4delf

should reverse-proxy to the Docker hosts' ${EDRN_PUBLISHED_PORT} with the
URL::

    /VirtualHostBase/https/edrn.nci.nih.gov:443/edrn/VirtualHostRoot/biomarkers/4delf

Some example for a couple common webservers follow.


Apache HTTPD Example
--------------------

Here's an example stanza for the Apache HTTPD web server::

    <VirtualHost *:443>
        ServerName edrn.nci.nih.gov
        ServerAlias edrn
        ServerAdmin nciappsupport@nih.gov
        DocumentRoot /var/www/html
        SSLEngine on
        …
        RewriteEngine on
        RewriteRule ^/(.*) http://DOCKERHOST:DOCKERPORT/VirtualHostBase/https/edrn.nci.nih.gov:443/edrn/VirtualHostRoot/$1 [L,P]
    </VirtualHost>

Replace DOCKERHOST with the hostname of the Docker environment running P5. 
Replace DOCKERPORT with the value of $EDRN_PUBLISHED_PORT. Don't forget to add
a redirect from ``http`` to ``https``.


NGINX Example
-------------

Here's an example excerpt for the Nginx web server::


    http {
        …
        upstream edrnDockerHost {
            server DOCKERHOST:DOCKERPORT;
        }
        …
        server {
            listen *:443;
            server_name edrn.nci.nih.gov;
            ssl on;
            …
            location / {
                rewrite ^(.*)$ /VirtualHostBase/https/edrn.nci.nih.gov:443/edrn/VirtualHostRoot/$1 break;
                proxy_pass http://edrnDockerHost;
            }
        }
    }

Replace DOCKERHOST with the hostname of the Docker environment running P5. 
Replace DOCKERPORT with the value of $EDRN_PUBLISHED_PORT. Don't forget to add
a redirect from ``http`` to ``https``.


❓ Questions, Comments, Etc.
=============================

If you run into any difficulties, you can contact the developer_ or the `EDRN
Informatics Center`_.  Bug reports and enhancement requests may also be filed
at the `issue tracker`_.


.. References:
.. _GitHub: https://github.com/EDRN/P5
.. _developer: mailto:sean.kelly@jpl.nasa.gov
.. _`EDRN Informatics Center`: mailto:ic-portal@jpl.nasa.gov
.. _`issue tracker`: https://github.com/EDRN/P5/issues


