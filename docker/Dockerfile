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

FROM alpine:3.19


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
    echo '@edge https://dl-cdn.alpinelinux.org/alpine/edge/main' >> /etc/apk/repositories &&\
    echo '@edge https://dl-cdn.alpinelinux.org/alpine/edge/community' >> /etc/apk/repositories &&\
    /sbin/apk update &&\
    :

RUN \
    build_deps="automake bzip2-dev cyrus-sasl-dev git g++ gcc libffi-dev libjpeg-turbo-dev libwebp-dev libxml2-dev libxslt-dev make musl-dev openjpeg-dev openldap-dev openssl-dev pcre-dev python3-dev postgresql-dev su-exec tiff-dev zlib-dev py3-pip" &&\
    run_deps="curl krb5-libs libgcc libjpeg-turbo libldap libpq libsasl libstdc++ libwebp libxml2 libxslt netcat-openbsd openjpeg python3 rsync tiff tidyhtml py3-gunicorn py3-flask" &&\
    py_deps="py3-numpy py3-pandas py3-pillow py3-psycopg2 py3-biopython" &&\
    /sbin/apk update --quiet &&\
    /sbin/apk add --no-progress --quiet --virtual /edrn-build $build_deps &&\
    /sbin/apk add --no-progress --quiet $run_deps &&\
    /sbin/apk add --no-progress --quiet $py_deps &&\
    :

# Over on GitHub Actions, we need to fail fast and not hit the six hour run limit, so make sure we got it right

RUN echo `/usr/bin/python3 --version` | grep -q '^Python 3\.11\.'
RUN echo `/usr/bin/python3 -c 'import numpy; print(numpy.__version__)'` | grep -q '^1\.25\.'
RUN echo `/usr/bin/python3 -c 'import pandas; print(pandas.__version__)'` | grep -q '^2\.0\.'
RUN echo `/usr/bin/python3 -c 'import PIL; print(PIL.__version__)'` | grep -q '^10\.3\.'
RUN echo `/usr/bin/python3 -c 'import psycopg2; print(psycopg2.__version__)'` | grep -q '^2\.9\.'
# Note that Biopython does not use MAJOR.MINOR.MICRO versions so there's no trailing dot here
RUN echo `/usr/bin/python3 -c 'import Bio; print(Bio.__version__)'` | grep -q '^1\.81'

RUN \
    : See https://github.com/python-ldap/python-ldap/issues/432 for workaround to Python LDAP vs OpenLDAP 2.5 issue &&\
    echo 'INPUT ( libldap.so )' > /usr/lib/libldap_r.so &&\
    /usr/bin/python3 -m venv --system-site-packages --upgrade-deps /app &&\
    /usr/bin/install -o edrn -g edrn -d /app/media /app/static /app/wheels &&\
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

RUN /app/bin/pip3 install --progress-bar off /app/wheels/edrnsite.controls-*.whl
RUN /app/bin/pip3 install --progress-bar off /app/wheels/edrnsite.streams-*.whl
RUN /app/bin/pip3 install --progress-bar off /app/wheels/edrnsite.content-*.whl
RUN /app/bin/pip3 install --progress-bar off /app/wheels/edrn.collabgroups-*.whl
RUN /app/bin/pip3 install --progress-bar off /app/wheels/edrn.theme-*.whl
RUN /app/bin/pip3 install --progress-bar off /app/wheels/edrnsite.ploneimport-*.whl
RUN /app/bin/pip3 install --progress-bar off /app/wheels/eke.geocoding-*.whl
RUN /app/bin/pip3 install --progress-bar off /app/wheels/eke.knowledge-*.whl
RUN /app/bin/pip3 install --progress-bar off /app/wheels/eke.biomarkers-*.whl
RUN /app/bin/pip3 install --progress-bar off /app/wheels/edrnsite.search-*.whl
RUN /app/bin/pip3 install --progress-bar off /app/wheels/edrn.metrics-*.whl
RUN /app/bin/pip3 install --progress-bar off /app/wheels/edrnsite.policy-*.whl

# And this too:

RUN \
    cd /app &&\
    : Get the static files ready &&\
    /sbin/su-exec edrn /usr/bin/env LDAP_BIND_PASSWORD=unused SIGNING_KEY=unused /app/bin/django-admin collectstatic --settings edrnsite.policy.settings.ops --no-input --clear --link &&\
    : Clean up clean up everybody everywhere &&\
    /sbin/apk del --quiet /edrn-build &&\
    /bin/rm -rf /app/wheels &&\
    /bin/rm -rf /var/cache/apk/* &&\
    /bin/chown -R edrn:edrn /app/lib/python3.*/site-packages &&\
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
ENTRYPOINT  ["/app/bin/python3"]
CMD         ["/usr/bin/gunicorn", "-c", "/app/gunicorn.conf.py"]
HEALTHCHECK --interval=5m --timeout=2m --start-period=10m CMD /usr/bin/curl --fail --retry 6 --max-time 5 --retry-delay 10 --retry-max-time 60 http://127.0.0.1:8000/ || /bin/sh -c 'killall5 -TERM && (/bin/sleep 10; killall5 -KILL)'


# Metadata
# --------
#
# Note that ``org.label-schema`` is deprecated, but it's a heck of a lot easier to understand. Still, why not just
# use the Dublin Core?

LABEL "org.label-schema.name"="EDRN Public Portal"
LABEL "org.label-schema.description"="Public website and knowledge environment for the Early Detecton Research Network"
LABEL "org.label-schema.version"="6.0.0"
