# encoding: utf-8

'''🧬 EDRN Site: development-mode settings

🚨 Do not use these settings in production you monster!
'''

from .base import *  # noqa: F401, F403


# Debug Mode
# ----------
#
# In development we want debug mode of course!
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#debug

DEBUG = True


# Templates
# ---------
#
# FEC practice: add a 'debug' flag to every template
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#templates
TEMPLATES = globals().get('TEMPLATES', [])
for t in TEMPLATES:  # noqa: F405
    t.setdefault('OPTIONS', {})
    t['OPTIONS']['debug'] = True


# Email Backend
# -------------
#
# How to send email while in debug mode: don't! The FEC practice: write emails to stdout.
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#email-backend

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# Site Identification
# -------------------
#
# 🔗 https://docs.wagtail.io/en/stable/reference/settings.html#wagtail-site-name

WAGTAIL_SITE_NAME = '🔧 Dev EDRN'


# Debugging & Development Tools
# -----------------------------
#
# The Django Debug Toolbar makes the site unbearably slow for development so it's disabled.
# To re-enable it, add `debug_toolbar` back to `INSTALLED_APPS` and also add back
# `debug_toolbar.middleware.DebugToolbarMiddleware` to `MIDDLEWARE`.
#
# 🔗 https://django-debug-toolbar.readthedocs.io/
# 🔗 https://docs.wagtail.io/en/stable/contributing/styleguide.html
# 🔗 https://pypi.org/project/django-extensions/
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#internal-ips

INSTALLED_APPS += [  # noqa
    # 'debug_toolbar',
    'wagtail.contrib.styleguide',
    'django_extensions',
]
MIDDLEWARE = [
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
] + globals().get('MIDDLEWARE', [])
INTERNAL_IPS = [
    # Needed by Django Debug Toolbar but not harmful to includ here:
    'localhost',
    '127.0.0.1',
    '::1'
]
