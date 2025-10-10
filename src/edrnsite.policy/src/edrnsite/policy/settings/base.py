# encoding: utf-8

'''🧬 EDRN Site: base settings'''

from .ldap import *  # noqa: F401, F403
import dj_database_url, os
import edrn.theme.settings as edrnThemeSettings
import edrnsite.content.settings as edrnSiteContentSettings
import edrnsite.streams.settings as edrnSiteStreamSettings
import eke.knowledge.settings as ekeKnowlegeSettings
import edrnsite.search.settings as edrnSiteSearchSettings
import eke.biomarkers.settings as ekeBiomarkersSettings


# Installed Applications
# ----------------------
#
# The "apps" (Python packages) enabled for Django.
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#installed-apps

INSTALLED_APPS = edrnSiteSearchSettings.INSTALLED_APPS + ekeKnowlegeSettings.INSTALLED_APPS + edrnThemeSettings.INSTALLED_APPS + [
    # Early Detection Research Network:
    'edrn.auth',
    'edrn.theme',
    'edrnsite.content',
    'edrnsite.controls',
    'edrnsite.search',
    'eke.knowledge',
    'eke.biomarkers',
    'edrnsite.ploneimport',
    'edrn.metrics',

    # Wagtail:
    'wagtail.contrib.redirects',
    'wagtail.contrib.settings',
    'wagtail.embeds',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',
    'wagtail',
    'taggit',
    'modelcluster',

    # Django:
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Sitemap generation
    'wagtail.contrib.sitemaps',
    'django.contrib.sitemaps',

    # Add-ons:
    'wagtail_modeladmin',          # Needed by wagtailmenus and wagtail-robots
    'wagtailmenus',                # Navigation menus
    'robots',                      # wagtail-robots's robots.txt handling
    'django_celery_results',       # Background task support (RDF ingest)
    'wagtail_favicon',             # Site icon, manifest.json, browser-config.xml support
    'wagtailmetadata',             # SEO enhancements

    # This Is Us™:
    'edrnsite.policy',
] + edrnSiteContentSettings.INSTALLED_APPS


# Middleware
# ----------
#
# Pipeline processors on the request/response.
#
# 🔗 https://docs.djangoproject.com/en/3.2/topics/http/middleware/

MIDDLEWARE = [
    # Django:
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Wagtail:
    'wagtail.contrib.redirects.middleware.RedirectMiddleware',
] + ekeKnowlegeSettings.MIDDLEWARE


# Frame Options
# -------------
#
# Needed for Plotly Dash
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#x-frame-options

X_FRAME_OPTIONS = ekeKnowlegeSettings.X_FRAME_OPTIONS


# Root URL Configuration
# ----------------------
#
# Name of the module that contains URL patterns.
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#root-urlconf

ROOT_URLCONF = 'edrnsite.policy.urls'


# Templates
# ---------
#
# The template engines and getting them going, etc.
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#templates

TEMPLATES = edrnThemeSettings.TEMPLATES + [
    {
        'NAME': 'edrnsite.policy',
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'wagtailmenus.context_processors.wagtailmenus',          # Needed by wagtaimenus, duh
                'wagtail.contrib.settings.context_processors.settings',  # For global settings
            ],
        },
    },
]


# Application for Web Services Gateway Interface
# ----------------------------------------------
#
# Full path to Python object that's the WSGI application.
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#wsgi-application

WSGI_APPLICATION = 'edrnsite.policy.wsgi.application'


# Type of Primary Key Field for Models
# ------------------------------------
#
# For models that don't have a primary key field, they get a default. This tells the data type
# of that field, `BigAutoField` in this case.
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Internationalization
# --------------------
#
# Settings for time zones, languages, locales, etc.
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#language-code
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-TIME_ZONE
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-USE_I18N
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-USE_L10N
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-USE_TZ

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_L10N      = True
USE_TZ        = True


# Databases
# ---------
#
# We let the magic of `dj-database-url` set this up for us. Note that `DATABASE_URL` will need to be
# provided in the environment.
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#databases
# 🔗 https://pypi.org/project/dj-database-url/

DATABASES = {'default': dj_database_url.config(default='postgresql://:@/edrn', conn_max_age=120)}  # seconds


# Authentication and Authorization
# --------------------------------
#
# Okay, deep breaths.

# Password Strength
# -----------------
#
# We don't use this because users keep creds in LDAP
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = []


# Site Identification
# -------------------
#
# 🔗 https://docs.wagtail.io/en/stable/reference/settings.html#wagtail-site-name

WAGTAIL_SITE_NAME = 'EDRN'


# Admin Base URL
# --------------
#
# 🔗 https://docs.wagtail.org/en/stable/reference/settings.html#wagtailadmin-base-url

WAGTAILADMIN_BASE_URL = os.getenv('BASE_URL', 'https://edrn.nci.nih.gov/')


# Static Files and Media
# ----------------------
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-STATIC_URL
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-STATIC_ROOT
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#media-root
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#media-url

STATIC_URL = os.getenv('STATIC_URL', '/static/')
MEDIA_URL = os.getenv('MEDIA_URL', '/media/')
STATIC_ROOT = os.getenv('STATIC_ROOT', os.path.join(os.path.abspath(os.getcwd()), 'static'))
MEDIA_ROOT = os.getenv('MEDIA_ROOT', os.path.join(os.path.abspath(os.getcwd()), 'media'))


# Migration Modules
# -----------------
#
# This shouldn't be necessary, but I am seeing the generated migrations code end up in the virtual
# environment and not in the source tree when running `make migrations` 🤨
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#migration-modules

MIGRATION_MODULES = {
    'edrnsite.policy': 'edrnsite.policy.migrations',
    **ekeKnowlegeSettings.MIGRATION_MODULES,
    **edrnSiteContentSettings.MIGRATION_MODULES,
    **edrnSiteStreamSettings.MIGRATION_MODULES,
    **edrnSiteSearchSettings.MIGRATION_MODULES,
    **ekeBiomarkersSettings.MIGRATION_MODULES,
}


# Logging
# -------
#
# There's got to be a better way to set this up tersely without clobbering existing settings while
# still be resilient in the face of no settings 😬
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-LOGGING

from django.utils.log import DEFAULT_LOGGING  # noqa
LOGGING = globals().get('LOGGING', DEFAULT_LOGGING)
loggers = LOGGING.get('loggers', {})
eke_knowledge = loggers.get('eke.knowledge', {})
eke_knowledge_handlers = set(eke_knowledge.get('handlers', []))
eke_knowledge_level = eke_knowledge.get('level', 'INFO')
eke_knowledge_handlers.add('console')
eke_knowledge['handlers'] = list(eke_knowledge_handlers)
eke_knowledge['level'] = eke_knowledge_level
loggers['eke.knowledge'] = eke_knowledge


# HTTP Subpath Support
# --------------------
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-FORCE_SCRIPT_NAME

fsn = os.getenv('FORCE_SCRIPT_NAME')
if fsn is not None: FORCE_SCRIPT_NAME = fsn


# Search
# ------
#
# 🔗 https://docs.wagtail.org/en/stable/reference/settings.html#wagtailsearch-backends

WAGTAILSEARCH_BACKENDS = edrnSiteSearchSettings.WAGTAILSEARCH_BACKENDS


# Message Queueing
# ----------------
#
# 🔗 https://docs.celeryproject.org/en/stable/django/index.html

CELERY_BROKER_URL = os.getenv('MQ_URL', 'redis://')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_TIMEZONE = TIME_ZONE


# Caching
# -------
#
# Note that in Django 3.2 Memcached is supported, and in 4.0 Redis becomes supported. However,
# we need Redis for both Celery and for distributed named locks (to prevent concurrent ingest).
# So we're "jumping ahead" with the Django-Redis add-on and using it for caching.
#
# Update: we're now on Django 4.0, however the cache support is rudimentary. We'll stick with
# ``django_redis`` for now.
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#caches
# 🔗 https://github.com/jazzband/django-redis

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('CACHE_URL', 'redis://'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient'
        }
    },
    'renditions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('CACHE_URL', 'redis://'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'MAX_ENTRIES': int(os.getenv('IMAGE_RENDITIONS_CACHE_SIZE', '1000')),
            'TIMEOUT': int(os.getenv('IMAGE_RENDITIONS_CACHE_TIMEOUT', '86400')),  # seconds
            # 'KEY_PREFIX': 'img-'  # Not sure if this is necessary
        }
    }
}

# Max upload number of fields
#
# Wagtail recommends bumping this to 10000, up from Django's default of 1000.
#
# This helps with complex page models that might hit the limit.
#
# 🔗 https://docs.wagtail.org/en/stable/reference/settings.html#max-upload-number-of-fields

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000


# CSRF
#
# 🔗 https://docs.djangoproject.com/en/4.1/ref/settings/#csrf-trusted-origins

CSRF_TRUSTED_ORIGINS = os.getenv(
    'CSRF_TRUSTED_ORIGINS', 'http://*.nci.nih.gov,https://*.nci.nih.gov,https://*.cancer.gov'
).split(',')


# reCAPTChA
#
# 🔗 https://github.com/springload/wagtail-django-recaptcha

RECAPTCHA_PUBLIC_KEY = os.getenv('RECAPTCHA_PUBLIC_KEY', '')
RECAPTCHA_PRIVATE_KEY = os.getenv('RECAPTCHA_PRIVATE_KEY', '')


# Email
#
# 🔗 https://docs.djangoproject.com/en/4.1/ref/settings/#email-host

EMAIL_HOST = os.getenv('EMAIL_HOST', 'mailfwd.nih.gov')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '25'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'False') == 'True'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False') == 'True'
