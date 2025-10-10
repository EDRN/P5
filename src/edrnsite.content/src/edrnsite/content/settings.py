# encoding: utf-8

'''😌 EDRN Site content's settings.'''


# Migration Modules
#
# This shouldn't be necessary, but I am seeing the generated migrations code end up in the virtual
# environment and not in the source tree when running `makemigrations` 🤨
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#migration-modules

MIGRATION_MODULES = {
    'edrnsite.content': 'edrnsite.content.migrations'
}


# Installed Applications
# ----------------------
#
# The "apps" (Python packages) enabled for Django.
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#installed-apps

INSTALLED_APPS = [
    'edrnsite.streams',
    'wagtail.contrib.table_block',
    'wagtail.contrib.typed_table_block',
    'wagtail.contrib.forms',
    'widget_tweaks',
    'wagtailcaptcha',
    'django_recaptcha',
]
