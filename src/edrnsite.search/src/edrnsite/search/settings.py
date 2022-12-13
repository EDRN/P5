# encoding: utf-8

'''🔍 EDRN Site search's settings.'''

import os


# Migration Modules
#
# This shouldn't be necessary, but I am seeing the generated migrations code end up in the virtual
# environment and not in the source tree when running `makemigrations` 🤨
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#migration-modules

MIGRATION_MODULES = {
    'edrnsite.search': 'edrnsite.search.migrations'
}


# Installed Applications
# ----------------------
#
# The "apps" (Python packages) enabled for Django.
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#installed-apps

INSTALLED_APPS = [
    'wagtail.contrib.search_promotions',  # Promote certain search results
]


# Search
# ------
#
# 🔗 https://docs.wagtail.org/en/stable/reference/settings.html#wagtailsearch-backends

WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.elasticsearch7',
        'AUTO_UPDATE': True,
        'ATOMIC_REBUILD': True,
        'INDEX': 'wagtail',
        'TIMEOUT': 5,
        'OPTIONS': {},
        'INDEX_SETTINGS': {},
        'URLS': [os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')]
    }
}
