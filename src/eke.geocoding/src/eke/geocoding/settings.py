# encoding: utf-8

'''🗺 EDRN Knowledge Environemnt's geocoding: settings'''


# Migration Modules
# -----------------
#
# This shouldn't be necessary, but I am seeing the generated migrations code end up in the virtual
# environment and not in the source tree when running `makemigrations` 🤨
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#migration-modules

MIGRATION_MODULES = {
    'eke.geocoding': 'eke.geocoding.migrations',
}
