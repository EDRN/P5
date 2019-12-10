#!/usr/bin/env python
# encoding: utf-8
# Copyright 2019 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from AccessControl.SecurityManagement import newSecurityManager, noSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy
from eke.knowledge.interfaces import IIngestor
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


# From https://docs.python.org/2/library/csv.html
class UTF8Recoder(object):
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")


# From https://docs.python.org/2/library/csv.html
class UnicodeReader(object):
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self


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


def _publish(context, workflowTool=None):
    try:
        if workflowTool is None: workflowTool = plone.api.portal.get_tool('portal_workflow')
        workflowTool.doActionFor(context, action='publish')
        context.reindexObject()
    except WorkflowException:
        pass
    if IFolderish.providedBy(context):
        for itemID, subItem in context.contentItems():
            _publish(subItem, workflowTool)


def _ingest(portal):
    u'''Do an RDF ingest of all of the folders listed in the registry key
    ``eke.knowledge.ingest.IPanel.objects`` regardless of whether ingest is on or off.
    '''
    registry = getUtility(IRegistry)
    paths = registry['eke.knowledge.interfaces.IPanel.objects']
    if not paths:
        logging.warn(u'No objects set in registry key eke.knowledge.interfaces.IPanel.objects; nothing to do')
        return
    for path in paths:
        logging.info(u'Ingesting %s', path)
        folder = portal.unrestrictedTraverse(path.encode('utf-8'))
        ingestor = IIngestor(folder)
        ingestor.ingest()
        transaction.commit()

    # Finally, make sure everything is indexed so they appear where they need
    # to be
    logging.info('Clearing and rebuilding the catalog')
    catalog = plone.api.portal.get_tool('portal_catalog')
    catalog.clearFindAndRebuild()


def _setSiteProposals(portal):
    u'''HK entered this stuff by hand on the old portal.'''
    # Organ or proposal text can be empty strings
    catalog = plone.api.portal.get_tool('portal_catalog')
    with open(os.path.join(os.environ['EDRN_PORTAL_HOME'], 'data', 'site-hand-info.csv'), 'rb') as f:
        reader = UnicodeReader(f)
        for row in reader:
            identifier, organs, proposal = row
            results = catalog(identifier=identifier, object_provides='eke.knowledge.site.ISite')
            if len(results) == 0:
                logging.info('No sites matching %s found; skipping', identifier)
                continue
            elif len(results) > 1:
                logging.critical('Multiple sites matching %s found (%d); should not happen', identifier, len(results))
                raise Exception('Multiple sites matching %s found (%d); should not happen' % (identifier, len(results)))
            else:
                site = results[0].getObject()
                site.organs = organs.split(u',')
                site.proposal = proposal
                site.reindexObject()


def _main(app):
    app = makerequest.makerequest(app)
    app.REQUEST['PARENTS'] = [app]
    setRequest(app.REQUEST)
    app.REQUEST.traverse('edrn')
    _setupZopeSecurity(app)
    portal = app['edrn']
    setSite(portal)
    _ingest(portal)
    _setSiteProposals(portal)
    noSecurityManager()
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
