# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environemnt: base knowledge's settings'''

import eke.geocoding.settings as ekeGeocodingSettings
import edrn.collabgroups.settings as edrnCollabGroupsSettings


# Migration Modules
#
# This shouldn't be necessary, but I am seeing the generated migrations code end up in the virtual
# environment and not in the source tree when running `makemigrations` 🤨
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#migration-modules

MIGRATION_MODULES = {
    'eke.knowledge': 'eke.knowledge.migrations',
    **edrnCollabGroupsSettings.MIGRATION_MODULES,
    **ekeGeocodingSettings.MIGRATION_MODULES,
}

# Installed Applications
# ----------------------
#
# The "apps" (Python packages) enabled for Django.
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#installed-apps

INSTALLED_APPS = [
    'django_plotly_dash.apps.DjangoPlotlyDashConfig',
    'django.contrib.humanize',
    'edrn.collabgroups',
    'eke.geocoding',
]


# Frame Options
# -------------
#
# Needed for Plotly Dash
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#x-frame-options

X_FRAME_OPTIONS = 'SAMEORIGIN'


# Middleware
# ----------
#
# Pipeline processors on the request/response; this is needed for Plotly Dash
#
# 🔗 https://docs.djangoproject.com/en/3.2/topics/http/middleware/

MIDDLEWARE = [
    'django_plotly_dash.middleware.BaseMiddleware',
]
