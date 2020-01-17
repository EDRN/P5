# EDRN P5 - Image Building
# ========================
#
# Used by "docker build"
#
# Basis
# -----
#
# Used to be based on Plone (Debian) 5.1.5, except that it specifies ``VOLUME /data``
# and CBIIT demands we run the internal container with username "edrn" with user ID
# 26013. Normally we would just ``adduser`` and ``chown`` except thanks to the
# ``VOLUME /data`` nothing we ``chown`` under ``/data`` takes effect and there's no
# way to undo a basis image's ``VOLUME`` (see this_). So now we have to reproduce
# every damn thing the ``plone/plone:5.1.5`` image does.
#
# That's what follows below.
#
# #16: also we now use python:2.7-slim-buster for security fixes
#
# FURTHER HEADACHE: we can't run as 26013 at JPL or any place else in the world
# because our data volume runs as 500, so let's throw Docker best practices out
# the window and make two images:
#
# ``Dockerfile`` (this file)
#     Makes an image the old fashioned way (user ID 500)
# ``Dockerfile-nci``
#     Makes an image with the user ID 26013 requirement


FROM python:2.7-slim-buster

ENV PIP=9.0.3 \
    ZC_BUILDOUT=2.11.4 \
    SETUPTOOLS=39.1.0 \
    WHEEL=0.31.1 \
    PLONE_MAJOR=5.1 \
    PLONE_VERSION=5.1.5 \
    PLONE_MD5=8ed5ff27fab67b1b510a1ce0ee2dd655

LABEL plone=$PLONE_VERSION \
    os="debian" \
    os.version="9" \
    name="Plone 5.1" \
    description="Plone image, based on Unified Installer" \
    maintainer="Plone Community"

RUN useradd --system -m -d /plone -U -u 500 edrn \
 && mkdir -p /plone/instance/ /data/filestorage /data/blobstorage

COPY buildout.cfg /plone/instance/

RUN buildDeps="dpkg-dev gcc libbz2-dev libc6-dev libjpeg62-turbo-dev libopenjp2-7-dev libpcre3-dev libssl-dev libtiff5-dev libxml2-dev libxslt1-dev wget zlib1g-dev" \
 && runDeps="gosu libjpeg62 libopenjp2-7 libtiff5 libxml2 libxslt1.1 lynx netcat poppler-utils rsync wv" \
 && apt-get update \
 && apt-get install -y --no-install-recommends $buildDeps \
 && wget -O Plone.tgz https://launchpad.net/plone/$PLONE_MAJOR/$PLONE_VERSION/+download/Plone-$PLONE_VERSION-UnifiedInstaller.tgz \
 && echo "$PLONE_MD5 Plone.tgz" | md5sum -c - \
 && tar -xzf Plone.tgz \
 && cp -rv ./Plone-$PLONE_VERSION-UnifiedInstaller/base_skeleton/* /plone/instance/ \
 && cp -v ./Plone-$PLONE_VERSION-UnifiedInstaller/buildout_templates/buildout.cfg /plone/instance/buildout-base.cfg \
 && pip install pip==$PIP setuptools==$SETUPTOOLS zc.buildout==$ZC_BUILDOUT wheel==$WHEEL \
 && cd /plone/instance \
 && buildout \
 && ln -s /data/filestorage/ /plone/instance/var/filestorage \
 && ln -s /data/blobstorage /plone/instance/var/blobstorage \
 && chown -R edrn:edrn /plone /data \
 && rm -rf /Plone* \
 && apt-get purge -y --auto-remove $buildDeps \
 && apt-get install -y --no-install-recommends $runDeps \
 && rm -rf /var/lib/apt/lists/* \
 && rm -rf /plone/buildout-cache/downloads/*

VOLUME /data

COPY docker-initialize.py docker-entrypoint.sh /

EXPOSE 8080
WORKDIR /plone/instance

HEALTHCHECK --interval=1m --timeout=5s --start-period=1m \
  CMD nc -z -w5 127.0.0.1 8080 || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["start"]

# And now we resume our friendly standard Dockerfile:
#
# Dependecies
# -----------
#
# Add additional build-time and run-time needs. The ``build-essential``
# is the build-time. The rest are run-time. We remove ``build-essential``
# at the end of the ``Dockerfile``.
#
# #16: Add backports+experimental, upgrade, and install steps for TwistLock security fixes
RUN echo 'deb http://deb.debian.org/debian buster-backports main' > /etc/apt/sources.list.d/backports.list && \
    echo 'deb http://deb.debian.org/debian experimental main' > /etc/apt/sources.list.d/experimental.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends libldap2-dev libsasl2-dev build-essential && \
    apt-get -y upgrade && \
    apt-get -t buster-backports install -y linux-libc-dev && \
    apt-get -t experimental install -y libjpeg62-turbo-dev libjpeg-dev


# Image Filesystem
# ----------------
#
# Prepare the file structure of the image with our custom Buildout config
# named ``docker.cfg``, its inclusions in ``etc``, the custom Plone source
# in ``src``.
COPY --chown=edrn:edrn docker.cfg /plone/instance
COPY --chown=edrn:edrn etc /plone/instance/etc
COPY --chown=edrn:edrn src /plone/instance/src


# Build
# -----
#
# Build everything out by first cleaning any host-provided Python objects
# and buildout detritus then running Buildout on the ``docker.cfg``.
RUN find /plone/instance/src -name '*.py[co]' -exec rm -f '{}' + && \
    pip install urllib3==1.25.7 && \
    rm -rf /plone/instance/src/*/{var,bin,develop-eggs,parts} && \
    rm -rf /plone/buildout-cache/eggs/urllib3-1.22* && \
    rm -rf /plone/buildout-cache/downloads/dist/urllib3-1.22* && \
    gosu edrn buildout -c docker.cfg

# TOD: do we need utf-8 sys.defaultencoding workaround??


# Cleanup
# -------
#
# We can now get rid of the build-time dependencies and leave the APT system
# in a clean state.
RUN apt-get remove -y --purge build-essential && \
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*


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
