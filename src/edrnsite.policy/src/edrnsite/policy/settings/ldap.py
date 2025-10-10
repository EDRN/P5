# encoding: utf-8

'''🧬 EDRN Site: Lightweight Directory Access Protocol settings'''

from django_auth_ldap.config import LDAPSearch, GroupOfUniqueNamesType
import ldap, os


# Wagtail Specific Settings
# -------------------------
#
# This ensures that Wagtail stays out of the way of LDAP
#
# 🔗 https://docs.wagtail.io/en/stable/reference/settings.html#wagtail-password-management-enabled
# 🔗 https://docs.wagtail.io/en/stable/reference/settings.html#wagtail-password-reset-enabled
# 🔗 https://docs.wagtail.io/en/stable/reference/settings.html#wagtailusers-password-enabled

WAGTAIL_PASSWORD_MANAGEMENT_ENABLED = False
WAGTAIL_PASSWORD_RESET_ENABLED      = False
WAGTAILUSERS_PASSWORD_ENABLED       = False


# Backends to Authenticate Against
# --------------------------------
#
# This says to try LDAP first, then the local site database.
#
# 🔗 https://docs.djangoproject.com/en/3.2/ref/settings/#authentication-backends

AUTHENTICATION_BACKENDS = ['django_auth_ldap.backend.LDAPBackend', 'django.contrib.auth.backends.ModelBackend']


# Server
# ------
#
# The timeout is in seconds.
#
# 🔗 https://django-auth-ldap.readthedocs.io/en/latest/authentication.html#server-config
# 🔗 https://django-auth-ldap.readthedocs.io/en/latest/reference.html#auth-ldap-cache-timeout

AUTH_LDAP_SERVER_URI = os.getenv('LDAP_URI', 'ldaps://edrn-ds.jpl.nasa.gov')
AUTH_LDAP_CACHE_TIMEOUT = int(os.getenv('LDAP_CACHE_TIMEOUT', '3600'))

# TLS Configuration for Self-Signed Certificates
# ------------------------------------------------
#
# These settings allow the LDAP client to work with self-signed certificates
# by disabling certificate verification. This is useful for local development
# but should be used with caution in production.
#
# 🔗 https://django-auth-ldap.readthedocs.io/en/latest/reference.html#auth-ldap-connection-options

# Only disable certificate verification for local development
uri = os.getenv('LDAP_URI', '')
if uri.startswith('ldaps://localhost') or uri.startswith('ldaps://host.docker.internal'):
    AUTH_LDAP_CONNECTION_OPTIONS = {
        ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER,
        ldap.OPT_X_TLS_NEWCTX: 0,
    }
    os.environ['LDAPTLS_REQCERT'] = 'never'
else:
    AUTH_LDAP_CONNECTION_OPTIONS = {}


# How to Find Users
# -----------------
#
# Normally we'd use AUTH_LDAP_USER_DN_TEMPLATE which is more efficient than binding with a manager
# DN and searching, but I cannot get the AUTH_LDAP_USER_DN_TEMPLATE to work with our LDAP server.
# So we're stuck going binding (and getting the credential) from the environment.
#
# Regardless, we keep AUTH_LDAP_ALWAYS_UPDATE_USER True so that LDAP values update Django `User`
# values.
#
# 🔗 https://django-auth-ldap.readthedocs.io/en/latest/reference.html#auth-ldap-always-update-user
# 🔗 https://django-auth-ldap.readthedocs.io/en/latest/reference.html#auth-ldap-user-dn-template
# 🔗 https://django-auth-ldap.readthedocs.io/en/latest/reference.html#auth-ldap-bind-dn
# 🔗 https://django-auth-ldap.readthedocs.io/en/latest/reference.html#auth-ldap-bind-password
# 🔗 https://django-auth-ldap.readthedocs.io/en/latest/reference.html#auth-ldap-user-search

AUTH_LDAP_ALWAYS_UPDATE_USER = True
# AUTH_LDAP_USER_DN_TEMPLATE = 'uid=%(user)s,dc=edrn,dc=jpl,dc=nasa,dc=gov'  # ← Wish this would work
AUTH_LDAP_USER_SEARCH = LDAPSearch('dc=edrn,dc=jpl,dc=nasa,dc=gov', ldap.SCOPE_ONELEVEL, '(uid=%(user)s)')
AUTH_LDAP_BIND_DN = os.getenv('LDAP_BIND_DN', 'uid=service,dc=edrn,dc=jpl,dc=nasa,dc=gov')
AUTH_LDAP_BIND_PASSWORD = os.getenv('LDAP_BIND_PASSWORD')
if AUTH_LDAP_BIND_PASSWORD is None:
    raise ValueError('The LDAP_BIND_PASSWORD environment variable must be set')

# Groups
# ------
#
# 🔗 https://django-auth-ldap.readthedocs.io/en/latest/reference.html#auth-ldap-group-search
# 🔗 https://django-auth-ldap.readthedocs.io/en/latest/reference.html#auth-ldap-group-type
# 🔗 https://django-auth-ldap.readthedocs.io/en/latest/reference.html#auth-ldap-find-group-perms
# 🔗 https://django-auth-ldap.readthedocs.io/en/latest/reference.html#auth-ldap-mirror-groups

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    'dc=edrn,dc=jpl,dc=nasa,dc=gov', ldap.SCOPE_ONELEVEL, '(objectClass=groupOfUniqueNames)'
)
AUTH_LDAP_GROUP_TYPE = GroupOfUniqueNamesType(name_attr='cn')
AUTH_LDAP_FIND_GROUP_PERMS = True
AUTH_LDAP_MIRROR_GROUPS = True


# Mapping User Attributes
# -----------------------
#
# This mapping is from Django user attribute name to LDAP attribute name. Note that we don't have a mapping
# for Django's `first_name` attribute in EDRN's LDAP.
#
# 🔗 https://django-auth-ldap.readthedocs.io/en/latest/reference.html#auth-ldap-user-attr-map

AUTH_LDAP_USER_ATTR_MAP = {
    'email':     'mail',
    'last_name': 'sn',
    'username':  'uid',
}


# Special Groups
# --------------
#
# These groups get special treatment in Django.
# 🔧 TODO: What should really go here? Users who are `Super User` can't seem to access the Django admin
# area, but `Portal Content Custodian` can 🤷‍♀️
#
#
# 🔗 https://django-auth-ldap.readthedocs.io/en/latest/reference.html#auth-ldap-user-flags-by-group

AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    'is_active':    'cn=All EDRN,dc=edrn,dc=jpl,dc=nasa,dc=gov',
    'is_staff':     'cn=Portal Content Custodian,dc=edrn,dc=jpl,dc=nasa,dc=gov',
    'is_superuser': 'cn=Super User,dc=edrn,dc=jpl,dc=nasa,dc=gov',
}
