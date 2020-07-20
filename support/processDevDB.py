#!/usr/bin/env python
# encoding: utf-8
# Copyright 2020 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from AccessControl.SecurityManagement import newSecurityManager, noSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy
from eke.knowledge.interfaces import IIngestor
from plone.app.viewletmanager.interfaces import IViewletSettingsStorage
from plone.registry.interfaces import IRegistry
from Products.CMFCore.interfaces import IFolderish
from Products.CMFCore.tests.base.security import PermissiveSecurityPolicy, OmnipotentUser
from Products.CMFCore.WorkflowCore import WorkflowException
from Testing import makerequest
from zope.component import getUtility
from zope.component.hooks import setSite
from zope.globalrequest import setRequest
import sys, logging, transaction, plone.api, csv, codecs, os, os.path


logging.basicConfig(level=logging.INFO, format='%(levelname)-8s %(message)s')
app = globals().get('app', None)  # ``app`` comes from ``instance run`` magic.


NO_ROBOTS = u'''User-agent: *
Disallow: /
'''


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


def setLDAPcacheParams(portal):
    logging.info('Setting memcached server for LDAP to localhost:11211')
    registry = getUtility(IRegistry)
    registry['pas.plugins.ldap.memcached'] = u'localhost:11211'


def disableSearchEngines(portal):
    logging.info('Disabling search engines')
    registry = getUtility(IRegistry)
    registry['plone.webstats_js'] = u''
    registry['plone.robots_txt'] = NO_ROBOTS


def showDevWarning(portal):
    storage = getUtility(IViewletSettingsStorage)
    skinName = portal.getCurrentSkinName() if portal.getCurrentSkinName() else 'Plone Default'
    hidden = list(storage.getHidden('plone.portaltop', skinName))
    try:
        hidden.remove('edrn.dev_warning')
        storage.setHidden('plone.portaltop', skinName, hidden)
    except ValueError:
        pass


def _main(app):
    # Apparently we don't need this; just do ``bin/zope-debug -O edrn run $PWD/support/upgradeEDRN.py``
    # app = makerequest.makerequest(app)
    # app.REQUEST['PARENTS'] = [app]
    # setRequest(app.REQUEST)
    # app.REQUEST.traverse('edrn')
    # _setupZopeSecurity(app)
    portal = app['edrn']
    # Don't need this either, thanks to ``-O edrn``
    # setSite(portal)
    setLDAPcacheParams(portal)
    disableSearchEngines(portal)
    showDevWarning(portal)
    # And don't need this:
    # noSecurityManager()
    transaction.commit()
    return True


def main(argv):
    _setupLogging()
    try:
        global app
        _main(app)
    except Exception as ex:
        logging.exception(u'This is most unfortunate: %s', unicode(ex))
        return False
    return True


if __name__ == '__main__':
    # The [2:] works around plone.recipe.zope2instance-4.2.6's lame bin/interpreter script issue
    sys.exit(0 if main(sys.argv[2:]) is True else -1)
