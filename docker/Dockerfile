# EDRN P5 - Image Building
# ========================
#
# Used by "docker image build" to create a containerizable image of the EDRN site.


# Basis
# -----
#
# Normally I'd use python:3.10-alpine3.15 as the basis for this image, except adding `numpy` as a dependency
# takes eons (well, 25 minutes on my MacBook Pro, but hits the 6 hour time limit on GitHub Actions). However,
# Alpine's own pakcaging system has a nice `py3-numpy` package that you can add in a second. (Why not use
# numpy's own Docker images? As of this writing (2022-01-26) they have just two images on hub.docker.com,
# neither are documented, no indication of what Python version they're for, and with the oddly named names of
# `numpy-gitpod` and `numpy-dev`—and I'm not going to use a `-dev` image in production.) See the `py_deps`
# below.

FROM alpine:3.16


# Configurable Arguments
# ----------------------
#
# - `user_id` should be either 26013 (National Cancer Institute) or 500 (rest of the world)

ARG user_id=26013


# Environment Variables
# ---------------------
#
# These don't need to be overridden

ENV PYTHONUNBUFFERED=1


# Layering
# --------
#
# Note that this project uses Python-LDAP 3.4.0 which only supports OpenLDAP 2.4, which reached end-of-life.
# Alpine Linux smartly incldues OpenLDAP 2.5. The `echo` in the `RUN` below works around this incompatibility.
# See https://github.com/python-ldap/python-ldap/issues/432#issuecomment-974799221
#
# The `py_deps` we install as APK packages instead of as dependencies of later `pip install` in order to
# save time.
#
# 🔮 TODO: these `build_deps` and `run_deps` feel excessive.

RUN \
    : Add system group edrn &&\
    /usr/sbin/addgroup -S -g $user_id edrn &&\
    : Add system user edrn, no password, home dir edrn, group edrn, gecos info "EDRN User" &&\
    /usr/sbin/adduser -S -D -h /edrn -G edrn -u $user_id -g 'EDRN User' edrn &&\
    : Dependencies &&\
    build_deps="automake bzip2-dev cyrus-sasl-dev g++ gcc libffi-dev libjpeg-turbo-dev libwebp-dev libxml2-dev libxslt-dev make musl-dev openjpeg-dev openldap-dev openssl-dev pcre-dev python3-dev postgresql-dev su-exec tiff-dev zlib-dev " &&\
    run_deps="curl krb5-libs libgcc libjpeg-turbo libldap libpq libsasl libstdc++ libwebp libxml2 libxslt lynx netcat-openbsd openjpeg python3 rsync tiff" &&\
    py_deps="py3-numpy py3-pandas py3-pillow py3-psycopg2" &&\
    /sbin/apk update --quiet &&\
    /sbin/apk add --no-progress --quiet --virtual /edrn-build $build_deps &&\
    /sbin/apk add --no-progress --quiet $run_deps &&\
    /sbin/apk add --no-progress --quiet $py_deps &&\
    : See https://github.com/python-ldap/python-ldap/issues/432 for workaround to Python LDAP vs OpenLDAP 2.5 issue &&\
    echo 'INPUT ( libldap.so )' > /usr/lib/libldap_r.so &&\
    /usr/bin/python3 -m ensurepip --upgrade &&\
    /usr/bin/pip3 install --quiet --progress-bar off --upgrade pip setuptools wheel &&\
    /usr/bin/pip3 install gunicorn==20.1.0 &&\
    /usr/bin/install -o edrn -g edrn -d /app /app/media /app/static /app/wheels &&\
    :

COPY --chown=edrn:edrn ./dist/*.whl /app/wheels/

# Normally a single RUN would work fine:
#
# RUN \
#     : Install our application-specific wheels &&\
#     /usr/bin/pip3 install --progress-bar off /app/wheels/* &&\
#     cd /app &&\
#     : Get the static files ready &&\
#     /sbin/su-exec edrn /usr/bin/env LDAP_BIND_PASSWORD=unused SIGNING_KEY=unused /usr/bin/django-admin collectstatic --settings edrnsite.policy.settings.ops --no-input --clear --link &&\
#     : Clean up clean up everybody everywhere &&\
#     /sbin/apk del --quiet /edrn-build &&\
#     /bin/rm -rf /app/wheels &&\
#     /bin/rm -rf /var/cache/apk/* &&\
#     :
#
# Except the Docker plugin for Jenkins at CBIIT chokes with an HTTP 400 error because apparently
# the single layer made above is too big. So, we have to do these in separate RUNs:

RUN /usr/bin/pip3 install --progress-bar off /app/wheels/edrnsite.controls-*.whl
RUN /usr/bin/pip3 install --progress-bar off /app/wheels/edrnsite.streams-*.whl
RUN /usr/bin/pip3 install --progress-bar off /app/wheels/edrnsite.content-*.whl
RUN /usr/bin/pip3 install --progress-bar off /app/wheels/edrn.auth-*.whl
RUN /usr/bin/pip3 install --progress-bar off /app/wheels/edrn.collabgroups-*.whl
RUN /usr/bin/pip3 install --progress-bar off /app/wheels/edrn.theme-*.whl
RUN /usr/bin/pip3 install --progress-bar off /app/wheels/edrnsite.ploneimport-*.whl
RUN /usr/bin/pip3 install --progress-bar off /app/wheels/eke.geocoding-*.whl
RUN /usr/bin/pip3 install --progress-bar off /app/wheels/eke.knowledge-*.whl
RUN /usr/bin/pip3 install --progress-bar off /app/wheels/eke.biomarkers-*.whl
RUN /usr/bin/pip3 install --progress-bar off /app/wheels/edrnsite.search-*.whl
RUN /usr/bin/pip3 install --progress-bar off /app/wheels/edrnsite.policy-*.whl

# And this too:

RUN \
    cd /app &&\
    : Get the static files ready &&\
    /sbin/su-exec edrn /usr/bin/env LDAP_BIND_PASSWORD=unused SIGNING_KEY=unused /usr/bin/django-admin collectstatic --settings edrnsite.policy.settings.ops --no-input --clear --link &&\
    : Clean up clean up everybody everywhere &&\
    : PrismaCloud does not like pip to be in the image &&\
    /usr/bin/pip3 uninstall --yes --quiet pip &&\
    /sbin/apk del --quiet /edrn-build &&\
    /bin/rm -rf /app/wheels &&\
    /bin/rm -rf /var/cache/apk/* &&\
    :

COPY --chown=edrn:edrn docker/*.py /app/


# Image Morphology
# ----------------
#
# Define external shape and other miscellaneous details of the image.

EXPOSE      8000
VOLUME      ["/app/media"]
USER        edrn
WORKDIR     /app
ENTRYPOINT  ["/usr/bin/gunicorn"]
HEALTHCHECK --interval=5m --timeout=2m --start-period=10m CMD /usr/bin/curl --fail --retry 6 --max-time 5 --retry-delay 10 --retry-max-time 60 http://127.0.0.1:8000/ || /bin/sh -c 'killall5 -TERM && (/bin/sleep 10; killall5 -KILL)'


# Metadata
# --------
#
# Note that ``org.label-schema`` is deprecated, but it's a heck of a lot easier to understand. Still, why not just
# use the Dublin Core?

LABEL "org.label-schema.name"="EDRN Public Portal"
LABEL "org.label-schema.description"="Public website and knowledge environment for the Early Detecton Research Network"
LABEL "org.label-schema.version"="6.0.0"
