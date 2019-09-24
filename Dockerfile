# EDRN P5 - Image Building
# ========================
#
# Used by "docker build" or "docker-compose build"

# Basis
# -----
#
# Based on Plone (Debian) 5.1.5
# This provides a ``EXPOSE 8080``, some ``ENV``, and an ``ENTRYPOINT`` and ``CMD``.
# It also specifies ``VOLUME /data``.
FROM plone/plone:5.1.5


# Dependecies
# -----------
#
# Add additional build-time and run-time needs. The ``build-essential``
# is the build-time. The rest are run-time. We remove ``build-essential``
# at the end of the ``Dockerfile``.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libldap2-dev libsasl2-dev build-essential


# Image Filesystem
# ----------------
#
# Prepare the file structure of the image with our custom Buildout config
# named ``docker.cfg``, its inclusions in ``etc``, the custom Plone source
# in ``src``.
COPY --chown=plone:plone docker.cfg /plone/instance
COPY --chown=plone:plone etc /plone/instance/etc
COPY --chown=plone:plone src /plone/instance/src


# Build
# -----
#
# Build everything out by first cleaning any host-provided Python objects
# and buildout detritus then running Buildout on the ``docker.cfg``.
RUN find /plone/instance/src -name '*.py[co]' -exec rm -f '{}' + \
    && rm -rf /plone/instance/src/*/{var,bin,develop-eggs,parts} \
    && gosu plone buildout -c docker.cfg

# TOD: do we need utf-8 sys.defaultencoding workaround??


# Cleanup
# -------
#
# We can now get rid of the build-time dependencies and leave the APT system
# in a clean state.
RUN apt-get remove -y --purge build-essential \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*


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
