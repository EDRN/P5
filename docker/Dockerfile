FROM python:3.13.7-trixie
ARG user_id=26013

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Only runtime libs (no compilers)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update --quiet --yes \
    && apt-get install --quiet --yes --no-install-recommends \
    ca-certificates \
    curl \
    gosu \
    libjpeg62-turbo \
    zlib1g \
    libtiff6 \
    libfreetype6 \
    libldap-dev \
    libwebp7 \
    libheif1 \
    libldap2 \
    libsasl2-dev \
    libssl3 \
    libzstd1 \
    && rm -rf /var/lib/apt/lists/*

# App layout & user
WORKDIR /app
RUN addgroup --system --gid ${user_id} edrn \
    && adduser --system --uid ${user_id} --ingroup edrn edrn \
    && install --owner=edrn --group=edrn --directory /app/media /app/static /app/wheels

# Install Gunicorn
RUN python -m venv /app &&\
    /app/bin/pip install --quiet --upgrade pip setuptools wheel build &&\
    /app/bin/pip install --quiet --progress-bar off "gunicorn==20.1.0"

# Copy prebuilt wheels
COPY --chown=edrn:edrn ./dist/*.whl /app/wheels/

RUN --mount=type=cache,target=/root/.cache/pip \
    /app/bin/pip install --progress-bar off /app/wheels/*.whl

# Collect static as the app user, clean up, and add a symlink for compatibility
RUN gosu edrn env LDAP_BIND_PASSWORD=unused SIGNING_KEY=unused /app/bin/django-admin collectstatic \
    --settings edrnsite.policy.settings.ops --no-input --clear --link \
    && rm -rf /app/wheels \
    && chown -R edrn:edrn /app \
    && ln -s /app/bin/django-admin /usr/bin/django-admin

# Runtime helpers / scripts
COPY --chown=edrn:edrn docker/*.py /app/

EXPOSE 8000
VOLUME ["/app/media"]
USER edrn
ENTRYPOINT ["/app/bin/gunicorn"]

HEALTHCHECK --interval=5m --timeout=2m --start-period=10m \
    CMD curl --fail --retry 6 --max-time 5 --retry-delay 10 --retry-max-time 60 http://127.0.0.1:8000/
