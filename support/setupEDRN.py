#!/usr/bin/env python
# encoding: utf-8
# Copyright 2019 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from AccessControl.SecurityManagement import newSecurityManager, noSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy
from node.ext.ldap.interfaces import ILDAPProps
from zope.component.hooks import setSite
from plone.app.dexterity.behaviors.exclfromnav import IExcludeFromNavigation
from Products.CMFCore.tests.base.security import PermissiveSecurityPolicy, OmnipotentUser
from Products.CMFPlone.factory import addPloneSite
from Testing import makerequest
from zope.event import notify
from zope.lifecycleevent import modified
import sys, logging, transaction, argparse, os, os.path, plone.api


logging.basicConfig(level=logging.INFO, format='%(levelname)-8s %(message)s')
app = globals().get('app', None)  # ``app`` comes from ``instance run`` magic.
_argParser = argparse.ArgumentParser(prog='admin.py', description=u'Adds a Manager user')
_argParser.add_argument('username', help=u'Zope admin user')
_argParser.add_argument('password', help=u"Zope admin password")
_argParser.add_argument('ldapPassword', help=u"LDAP password")


_EXTENSION_IDS = [
    'plonetheme.barceloneta:default', 'plone.app.caching:default', 'edrnsite.policy:default'
]
_TO_IMPORT = (
    'about-edrn',
    'advocates',
    'beta',
    'cancer-bioinformatics-workshop',
    'c-edrn',
    'docs',
    'EDRN RFA guidelines-v4.pdf',
    'FOA-guidelines',
    'funding-opportunities',
    'informatics',
    'microrna',
    'network-consulting-team',
    'new-user-information',
    'researchers',
    'resources',
    'secretome'
)


def _setupLogging():
    channel = logging.StreamHandler()
    channel.setFormatter(logging.Formatter('%(asctime)-15s %(levelname)-8s %(message)s'))
    logger = logging.getLogger('jpl')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(channel)


def _setupZopeSecurity(app):
    logging.info(u'Setting up Zope security')
    acl_users = app.acl_users
    setSecurityPolicy(PermissiveSecurityPolicy())
    newSecurityManager(None, OmnipotentUser().__of__(acl_users))


def _nukeAdmins(app):
    logging.info(u'Remove old admin users')
    acl_users = app.acl_users
    acl_users.userFolderDelUsers(acl_users.getUserNames())
    transaction.commit()


def _installAdmin(app, username, password):
    logging.info(u'Installing new admin user named %s with password %s', username, password)
    acl_users = app.acl_users
    acl_users.userFolderAddUser(username, password, ['Manager'], [])
    transaction.commit()


def _createEDRNSite(app):
    if 'edrn' in app.keys():
        logging.info('Object with key "edrn" already found in Zope app server; not adding an EDRN site')
        return app['edrn']
    site = addPloneSite(
        app,
        'edrn',
        u'Early Detection Research Network',
        u'Biomarkers: the key to early detection',
        extension_ids=_EXTENSION_IDS,
        setup_content=False
    )
    transaction.commit()
    logging.info('Created site %r', site)
    return site


def _setLDAPPassword(portal, password):
    logging.debug('Getting LDAP plugin from portal "%s"', portal)
    if 'acl_users' not in portal.keys():
        logging.critical('No "acl_users" in this portal; is this even Plone?')
        return False
    acl_users = portal['acl_users']
    if 'pasldap' not in acl_users.keys():
        logging.critical('No "pasldap" found in acl_users; is "pas.plugins.ldap" installed?')
        return False
    pasldap = acl_users['pasldap']
    props = ILDAPProps(pasldap)
    logging.debug('Setting LDAP password')
    props.password = password
    transaction.commit()
    # notify(modified(acl_users))
    return True


def _loadZEXPFiles(portal):
    zexpDir = os.environ.get('ZEXP_EXPORTS', '/usr/local/edrn/portal/zexp-exports')
    for objID in _TO_IMPORT:
        if objID in portal.keys():
            logging.info('Path "/%s" already exists in portal; skipping zexp import of it', objID)
            continue
        zexpFile = os.path.join(zexpDir, objID + '.zexp')
        if not os.path.isfile(zexpFile):
            logging.warn('Zexp file "%s" does not exist (or is not a file); skipping import', zexpFile)
            continue
        logging.info('Importing zexp file "%s" to portal path "/%s"', zexpFile, objID)
        portal._importObjectFromFile(zexpFile)
        transaction.commit()
        # notify(modified(portal))
    logging.info('Clearing and rebuilding the catalog')
    catalog = plone.api.portal.get_tool('portal_catalog')
    catalog.clearFindAndRebuild()
    logging.info('Done importing ZEXP files')
    transaction.commit()


def _tuneUp(portal):
    if 'network-consulting-team' in portal.keys():
        logging.info('Removing network-consulting-team from navigation')
        folder = portal['network-consulting-team']
        adapter = IExcludeFromNavigation(folder, None)
        if adapter is not None:
            adapter.exclude_from_nav = True
            # notify(modified(folder))
    transaction.commit()
    return True


def _setupEDRN(app, username, password, ldapPassword):
    app = makerequest.makerequest(app)
    _setupZopeSecurity(app)
    _nukeAdmins(app)
    _installAdmin(app, username, password)
    portal = _createEDRNSite(app)
    setSite(portal)
    _loadZEXPFiles(portal)  # Stack traces; see https://community.plone.org/t/stack-trace-when-loading-zexp-from-a-script/8060
    _setLDAPPassword(portal, ldapPassword)
    _tuneUp(portal)
    noSecurityManager()
    transaction.commit()


def main(argv):
    _setupLogging()
    try:
        global app
        args = _argParser.parse_args(argv[1:])
        _setupEDRN(app, args.username, args.password, args.ldapPassword)
    except Exception as ex:
        logging.exception(u'This sucks: %s', unicode(ex))
        return False
    return True


if __name__ == '__main__':
    # The [2:] works around plone.recipe.zope2instance-4.2.6's lame bin/interpreter script issue
    sys.exit(0 if main(sys.argv[2:]) is True else -1)
