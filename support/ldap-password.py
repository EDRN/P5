# encoding: utf-8
#
# Run this with ``zope-debug run support/ldap-password.py``
#

# imports

from AccessControl.SecurityManagement import newSecurityManager, noSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy
from getpass import getpass
from node.ext.ldap.interfaces import ILDAPProps
from Products.CMFCore.tests.base.security import PermissiveSecurityPolicy, OmnipotentUser
from Testing import makerequest
from zope.component.hooks import setSite
from Products.CMFPlone.factory import addPloneSite
import transaction, logging, sys


# Logging

_logger = logging.getLogger('ldap-password')
_logger.setLevel(logging.DEBUG)
_console = logging.StreamHandler(sys.stderr)
_formatter = logging.Formatter('%(levelname)-8s %(message)s')
_console.setFormatter(_formatter)
_logger.addHandler(_console)


# Zope

APP = globals().get('app', None) # ``app`` comes from ``instance run`` magic.
PORTAL_ID = 'edrn'
PORTAL_TITLE = 'EDRN'
PORTAL_DESCRIPTION = 'Early Detection Research Network'
EXTENSION_IDS = (
    'plonetheme.barceloneta:default',
    'edrnsite.policy:default'
)


# Let's do this

def setupZopeSecurity(app):
    _logger.debug('Setting up Zope security')
    acl_users = app.acl_users
    setSecurityPolicy(PermissiveSecurityPolicy())
    newSecurityManager(None, OmnipotentUser().__of__(acl_users))


def getPortal(app, portalID):
    _logger.debug('Getting portal "%s"', portalID)
    try:
        portal = getattr(app, portalID)
    except AttributeError:
        _logger.debug('Portal "%s" not found, creating it', portalID)
        portal = addPloneSite(app, portalID, PORTAL_TITLE, PORTAL_DESCRIPTION,
            extension_ids=EXTENSION_IDS)
    setSite(portal)
    return portal


def setLDAPPassword(portal, password):
    _logger.debug('Getting LDAP plugin from portal "%s"', portal)
    if 'acl_users' not in portal.keys():
        _logger.critical('No "acl_users" in this portal; is this even Plone?')
        return False
    acl_users = portal['acl_users']
    if 'pasldap' not in acl_users.keys():
        _logger.critical('No "pasldap" found in acl_users; is "pas.plugins.ldap" installed?')
        return False
    pasldap = acl_users['pasldap']
    props = ILDAPProps(pasldap)
    _logger.debug('Setting LDAP password')
    props.password = password
    transaction.commit()
    return True


def main(argv):
    _logger.debug('argv = %s', repr(argv))
    if len(argv) == 2:
        password = argv[1]
    elif len(argv) == 1:
        password = getpass('LDAP manager password: ')
    else:
        print >>sys.stderr, u'Usage: %s [password]' % argv[0]
        print >>sys.stderr, u"If password is not supplied on the command-line (and it shouldn't be)"
        print >>sys.stderr, u"you'll be prompted for the LDAP manager password."
        return False
    global APP, PORTAL_ID
    app = makerequest.makerequest(APP)
    setupZopeSecurity(app)
    portal = getPortal(app, PORTAL_ID)
    rc = setLDAPPassword(portal, password)
    noSecurityManager()
    _logger.debug('Done, rc = %r', rc)
    return rc


if __name__ == '__main__':
    sys.exit(0 if main(sys.argv[2:]) is True else -1)
