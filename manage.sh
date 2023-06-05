#!/bin/sh -e
#
#
# Run django-admin locally with this convenience script

. ${HOME}/.secrets/passwords.sh

export DJANGO_SETTINGS_MODULE=local
export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY RECAPTCHA_PRIVATE_KEY RECAPTCHA_PUBLIC_KEY

if [ ! -d "src" -o ! -d "etc" -o ! -d "docker" ]; then
    echo "🚨 Run this from the checked-out EDRN portal source directory" 1>&2
    echo "You should have these subdirs in the current directory: src etc docker" 1>&2
    exit 1
fi

if [ -d ".venv/lib/python3.10/site-packages/edrnsite" -o -d ".venv/lib/python3.10/site-packages/eke" ]; then
    echo "⚠️ Somehow in-development eggs got expanded in the site-packages dir!" 1>&2
    echo "Nuking the .venv so we're forced to start over" 1>&2
    rm -rf ".venv"
fi

if [ ! -d ".venv" ]; then
    echo "⚠️ Local Python virtual environment missing; attempting to re-create it" 1>&2
    python3.10 -m venv .venv
    .venv/bin/pip install --quiet --upgrade setuptools pip wheel build
    # We cannot do these in one command; it results in pip expanding the `eke` directory in the .venv
    # and no longer being in "editable" mode.
    .venv/bin/pip install --editable 'src/eke.geocoding[dev]'
    .venv/bin/pip install --editable 'src/edrnsite.streams[dev]'
    .venv/bin/pip install --editable 'src/edrnsite.controls[dev]'
    .venv/bin/pip install --editable 'src/edrnsite.content[dev]'
    .venv/bin/pip install --editable 'src/edrn.auth[dev]'
    .venv/bin/pip install --editable 'src/edrn.collabgroups[dev]'
    .venv/bin/pip install --editable 'src/eke.knowledge[dev]'
    .venv/bin/pip install --editable 'src/eke.biomarkers[dev]'
    .venv/bin/pip install --editable 'src/edrnsite.search[dev]'
    .venv/bin/pip install --editable 'src/edrn.theme[dev]'
    .venv/bin/pip install --editable 'src/edrnsite.ploneimport[dev]'
    .venv/bin/pip install --editable 'src/edrn.metrics[dev]'
    .venv/bin/pip install --editable 'src/edrnsite.policy[dev]'
    .venv/bin/pip install --editable 'src/edrnsite.test[dev]'

    # When wagtail/wagtail#10184 is fixed, we can remove this:
    patch --directory ${PWD}/.venv/lib/python3.10/site-packages --input ${PWD}/patches/wagtail-users-utils.patch --strip 0
fi

command="$1"
shift
exec /usr/bin/env \
    LDAP_BIND_PASSWORD="$edrn_service_password" \
    DATABASE_URL="postgresql://:@/edrn" \
    ".venv/bin/django-admin" $command --settings local --pythonpath . "$@"


