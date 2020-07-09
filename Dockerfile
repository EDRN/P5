# EDRN P5 - Image Building
# ========================
#
# Used by "docker image build"
#
# Basis
# -----
#
# Used to be based on Plone (Debian) 5.1.5, except that it specifies
# ``VOLUME /data`` and CBIIT demands we run the internal container with
# username "edrn" with user ID 26013. Normally we would just ``adduser`` and
# ``chown`` except thanks to the ``VOLUME /data`` nothing we ``chown`` under
# ``/data`` takes effect and there's no way to undo a basis image's ``VOLUME``
# (see this_). So now we have to reproduce every damn thing the
# ``plone/plone:5.1.5`` image does.
#
# .. _this: https://github.com/moby/moby/issues/3465#issuecomment-45554646
#
# BUT WAIT THERE'S MORE!
#
# The Twit-lock security scanner absolutely hates Debian Linux, so we can't
# base ourselves off the python:2.7 image either, which uses Debian. Further
# tests show that Ubuntu is out too (of course); the only acceptable Linuxes
# are centos:8 and alpine:3. So we either have to install Python, Plone, and
# all our dependencies on centos:8 or use the python:2.7.17-alpine3.11 as a
# base.
#
# That's what follows below.
#
# FURTHER HEADACHE: we can't run as 26013 at JPL or any place else in the
# world because our data volume runs as 500, so let's throw Docker best
# practices out the window and make two images:
#
# ``Dockerfile`` (this file)
#     Makes an image the old fashioned way (user ID 500)
# ``Dockerfile-nci``
#     Makes an image with the user ID 26013 requirement

# Basis
# -----
#
# We'd normally just ue plone:5.1.5 but see the "diatribe" above.

FROM python:2.7.17-alpine3.11


# Versions and digests
# --------------------
#
# The urllib3 is to get around a Twit-lock security flag
# And urllib3 1.25.7 → 1.25.9 is another Twit-lock security flag

ENV \
    URLLIB3=1.25.9 \
    PIP=9.0.3 \
    ZC_BUILDOUT=2.11.4 \
    SETUPTOOLS=39.1.0 \
    WHEEL=0.31.1 \
    PLONE_MAJOR=5.1 \
    PLONE_VERSION=5.1.5 \
    PLONE_MD5=8ed5ff27fab67b1b510a1ce0ee2dd655


# Plone and EDRN Setup
# --------------------
#
# OK, now that we have a working Python, let's change it up.
#
# Users and Directories
# ~~~~~~~~~~~~~~~~~~~~~
#
# See note above; for NCI we change to 26013 instead of 500

RUN : &&\
    addgroup -S -g 500 edrn &&\
    adduser -S -D -h /plone -G edrn -u 500 -g 'Plone for EDRN User' edrn &&\
    mkdir -p /plone/instance /data/filestorage /data/blobstorage


# Our Code
# ~~~~~~~~
#
# The ``etc`` and ``src`` directories are our own, as is the ``docker.cfg``;
# the ``buildout.cfg`` is duplicated from plone/plone.docker, as is the
# ``docker-initialize.py`` and the (modified) ``docker-entrypoint.sh``.

COPY --chown=edrn:edrn buildout.cfg docker.cfg /plone/instance/
COPY --chown=edrn:edrn etc /plone/instance/etc
COPY --chown=edrn:edrn src /plone/instance/src
COPY docker-initialize.py docker-entrypoint.sh /


# Buildout
# ~~~~~~~~
#
# Now we build everything out. This is a big layer! Be patient, it downloads,
# installs, extracts, compiles, and more.

RUN : &&\
    echo '@testing http://dl-cdn.alpinelinux.org/alpine/edge/testing' >> /etc/apk/repositories &&\
    echo '@edge http://dl-cdn.alpinelinux.org/alpine/edge/main' >> /etc/apk/repositories &&\
    apk update &&\
    : More Twit-lock &&\
    apk del tiff &&\
    : We will uninstall these later &&\
    buildDeps="gcc bzip2-dev musl-dev libjpeg-turbo-dev openjpeg-dev pcre-dev openssl-dev tiff-dev libxml2-dev libxslt-dev zlib-dev openldap-dev cyrus-sasl-dev libffi-dev" &&\
    apk add --virtual plone-build $buildDeps &&\
    : These stay &&\
    runDeps="openjpeg@edge libldap libsasl libjpeg-turbo tiff libxml2 libxslt lynx netcat-openbsd libstdc++@edge libgcc@edge sqlite-libs@edge poppler-utils@edge rsync wv su-exec bash" &&\
    apk add $runDeps &&\
    : Get, check, and extract Plone &&\
    wget -q -O Plone.tgz https://launchpad.net/plone/$PLONE_MAJOR/$PLONE_VERSION/+download/Plone-$PLONE_VERSION-UnifiedInstaller.tgz &&\
    echo "$PLONE_MD5  Plone.tgz" | md5sum -c - &&\
    tar -xzf Plone.tgz &&\
    cp -r ./Plone-$PLONE_VERSION-UnifiedInstaller/base_skeleton/* /plone/instance/ &&\
    cp ./Plone-$PLONE_VERSION-UnifiedInstaller/buildout_templates/buildout.cfg /plone/instance/buildout-base.cfg &&\
    : Clean up anything copied from our src dirs &&\
    find /plone/instance/src -name '*.py[co]' -exec rm -f '{}' + &&\
    rm -rf /plone/instance/src/*/{var,bin,develop-eggs,parts} &&\
    : Install buildout, setuptools, and pip at specific versions &&\
    pip --quiet install pip==$PIP setuptools==$SETUPTOOLS zc.buildout==$ZC_BUILDOUT wheel==$WHEEL urllib3==$URLLIB3 &&\
    cd /plone/instance &&\
    buildout &&\
    buildout -c docker.cfg &&\
    ln -s /data/filestorage/ /plone/instance/var/filestorage &&\
    ln -s /data/blobstorage /plone/instance/var/blobstorage &&\
    chown -R edrn:edrn /plone /data &&\
    rm -rf /Plone* &&\
    apk del plone-build &&\
    rm -rf /plone/buildout-cache/downloads/* /var/cache/apk/* &&\
    :


# Context
# -------
#
# Finally, we set up the runtime context: volume, cwd, etc.

VOLUME      /data
EXPOSE      8080
USER        edrn:edrn
WORKDIR     /plone/instance
HEALTHCHECK --interval=1m --timeout=5s --start-period=1m CMD nc -z -w5 127.0.0.1 8080 || exit 1
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD        ["start"]


# Metadata
# --------
#
# Note that ``org.label-schema`` is deprecated, but it's a heck of a lot
# easier to understand.  Still, I have to wonder why they didn't just use
# Dublin Core.

LABEL "org.label-schema.name"="EDRN Public Portal Power Level 5"
LABEL "org.label-schema.description"="Plone 5-based portal for the Early Detecton Research Network"
LABEL "org.label-schema.version"="5.0.0"
LABEL "org.label-schema.schema-version"="1.0"
LABEL "org.label-schema.docker.cmd"="docker run --detach --publish 2345:8080 --volume ${EDRN_DATA_DIR}/filestorage:/data/filestorage --volume ${EDRN_DATA_DIR}/blobstorage:/data/blobstorage --volume ${EDRN_DATA_DIR}/log:/data/log edrn-p5"


# Dependencies
# ------------
#
# To figure this out, first set up a throwaway Debian container and run::
#     apt-get update
#     apt-get install apt-file
#     apt-file update
# Then for a package X::
#     apt-get install X
#     apt-file list X
# And pick a sentinel file from the list. Plug that into https://pkgs.alpinelinux.org/contents
# to find out what Alpine package provides that file.
#
# Key: debian-package sentinel-file alpine-package
#
# Build Time
# ~~~~~~~~~~
#
# From Plone's Dockerfile:
# gcc                   /usr/bin/gcc            gcc
# libbz2-dev            /usr/include/bzlib.h                    bzip2-dev
# libc6-dev             /usr/include/signal.h                   musl-dev
# libjpeg62-turbo-dev   /usr/include/jerror.h                   libjpeg-turbo-dev
# libopenjp2-7-dev      /usr/include/openjpeg-2.3/openjpeg.h    openjpeg-dev
# libpcre3-dev          /usr/include/pcre.h                     pcre-dev
# libssl-dev            /usr/include/openssl/ssl.h              openssl-dev
# libtiff5-dev          "transitional package"; try tiff.h      tiff-dev
# libxml2-dev           /usr/bin/xml2-config                    libxml2-dev
# libxslt1-dev          /usr/bin/xslt-config                    libxslt-dev
# wget                  /usr/bin/wget                           wget (is this really build dep?)*
# zlib1g-dev            /usr/include/zlib.h                     zlib-dev
#
# Implicit deps:
# libffi-dev            /usr/include/x86_64-linux-gnu/ffi.h     libffi-dev
#
# ALSO: wget is BusyBox! Do we need the full wget?
# dpkg-dev?
#
# Our own additional needs for P5:
#
# libldap2-dev          /usr/include/ldap.h                     openldap-dev
# libsasl2-dev          /usr/include/sasl/sasl.h                cyrus-sasl-dev
#
# Run Time
# ~~~~~~~~
#
# gosu                  /usr/sbin/gosu                          gosu@testing
# libjpeg62             libjpeg.so                              libjpeg-turbo
# libopenjp2-7          libopenjp2.so                           openjpeg
# libtiff5              libtiff.so                              tiff
# libxml2               libxml2.so                              libxml2
# libxslt1.1            libxslt.so                              libxslt
# lynx                  /usr/bin/lynx                           lynx
# netcat (virtual)      /usr/bin/nc                             netcat-openbsd
# poppler-utils         /usr/bin/pdftohtml                      poppler-utils@edge
# rsync                 /usr/bin/rsync                          rsync
# wv                    /usr/bin/wvHtml                         wv


