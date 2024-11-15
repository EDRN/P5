# encoding: utf-8

'''🧬 EDRN Site: ops-mode settings'''

from .base import *  # noqa: F401, F403
import os


# Debug Mode
# ----------
#
# This had better be off! TURN THIS BACK TO FALSE!!!
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#debug

DEBUG = False


# Secret Key
# ----------
#
# Used to sign sessions, etc. In production this comes from the environment and presumably
# Docker sets it. If it's not set, the default is to use `None`, which'll make Django abort,
# which is what we want, because this absolutely has to be set!
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-SECRET_KEY

SECRET_KEY = os.getenv('SIGNING_KEY')
if SECRET_KEY is None:
    raise ValueError('🚨 In operations, the SIGNING_KEY variable cannot be unset')


# Handling of Session Keys
# ------------------------
#
# In production, we want cookies to be sent securely and only over HTTP (sorry JavaScript)—and
# similarly for CSRF cookies.
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#session-cookie-secure
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-SESSION_COOKIE_HTTPONLY
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#csrf-cookie-secure
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#csrf-cookie-httponly

_secure = os.getenv('SECURE_COOKIES', 'True') == 'True'
SESSION_COOKIE_SECURE = SESSION_COOKIE_HTTPONLY = CSRF_COOKIE_SECURE = CSRF_COOKIE_HTTPONLY = _secure
del _secure


# Allowed Hosts
# -------------
#
# Valid `Host:` headers that we'll serve
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-ALLOWED_HOSTS

ALLOWED_HOSTS = [i.strip() for i in os.getenv('ALLOWED_HOSTS', '.nci.nih.gov,.cancer.gov').split(',')]
