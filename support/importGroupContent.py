#!/usr/bin/env python
# encoding: utf-8
# Copyright 2019 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from AccessControl.SecurityManagement import newSecurityManager, noSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer
from plone.namedfile.file import NamedBlobFile
from Products.CMFCore.interfaces import IFolderish
from Products.CMFCore.tests.base.security import PermissiveSecurityPolicy, OmnipotentUser
from Products.CMFCore.WorkflowCore import WorkflowException
from Testing import makerequest
from zope.component.hooks import setSite
from zope.globalrequest import setRequest
import sys, logging, transaction, plone.api, os.path, json


# logging.basicConfig(level=logging.INFO, format='%(levelname)-8s %(message)s')
app = globals().get('app', None)  # ``app`` comes from ``instance run`` magic.


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


def _publish(context, workflowTool=None, action='publish'):
    try:
        if workflowTool is None: workflowTool = plone.api.portal.get_tool('portal_workflow')
        workflowTool.doActionFor(context, action=action)
        context.reindexObject()
    except WorkflowException:
        pass
    if IFolderish.providedBy(context):
        for itemID, subItem in context.contentItems():
            _publish(subItem, workflowTool, action)


def _getEntryType(fromFolder):
    typeIndicator = os.path.join(fromFolder, 'TYPE.txt')
    if not os.path.isfile(typeIndicator): return None
    with open(typeIndicator, 'r') as f:
        return f.read()


def _getMetadata(fromFolder, filename='metadata.json'):
    metadataFile = os.path.join(fromFolder, filename)
    if not os.path.isfile(metadataFile): return None
    with open(metadataFile, 'rb') as f:
        return json.load(f)


def _doFolderImport(parent, fsFolder):
    metadata = _getMetadata(fsFolder)
    assert metadata is not None, u'No metadata found for %s' % fsFolder
    folder = createContentInContainer(parent, 'Folder', title=metadata['title'], description=metadata['description'])
    _doGroupImport(folder, fsFolder)


def _doGroupEventImport(parent, fsFolder):
    metadata = _getMetadata(fsFolder, 'EVENT.json')
    folder = createContentInContainer(parent, 'Folder', title=metadata['title'], description=metadata['description'])
    event = createContentInContainer(
        folder,
        'Event',
        attendees=metadata['attendees'],
        contact_email=metadata['contactEmail'],
        contact_name=metadata['contactName'],
        contact_phone=metadata['contactPhone'],
        description=metadata['description'],
        event_url=metadata['eventUrl'],
        location=metadata['location'],
        text=RichTextValue(metadata['text'], 'text/html', 'text/x-html-safe'),
        title=metadata['title']
    )
    folder.setDefaultPage(event.id)
    _doGroupImport(folder, fsFolder)


def _doFileImport(folder, fsFolder):
    metadata = _getMetadata(fsFolder)
    with open(os.path.join(fsFolder, 'file.dat'), 'rb') as f:
        createContentInContainer(
            folder,
            'File',
            title=metadata['title'],
            description=metadata['description'],
            file=NamedBlobFile(f.read(), filename=metadata['filename'], contentType=metadata['contentType'])
        )


def _doHighlightImport(folder, fsFolder):
    metadata = _getMetadata(fsFolder, 'HIGHLIGHT.json')
    highlight = createContentInContainer(
        folder,
        'News Item',
        title=metadata['title'],
        description=metadata['description'],
        text=RichTextValue(metadata['text'], 'text/html', 'text/x-html-safe')
    )
    _publish(highlight)


def _doGroupImport(folder, fsFolder):
    for entryName in os.listdir(fsFolder):
        entry = os.path.join(fsFolder, entryName)
        if os.path.isdir(entry):
            entryType = _getEntryType(entry)
            assert entryType is not None and len(entryType) > 0
            if entryType == 'Folder':
                _doFolderImport(folder, entry)
            elif entryType == 'Group Event':
                _doGroupEventImport(folder, entry)
            elif entryType == 'File':
                _doFileImport(folder, entry)
            elif entryType == 'Highlight':
                _doHighlightImport(folder, entry)
            else:
                assert False, u'Bad entry type {}'.format(entryType)


def _importGroupContent(portal, groupContent):
    logging.debug(u'Importing group content from "%s"', groupContent)
    try:
        groups = portal.unrestrictedTraverse('groups')
        for groupID in groups.keys():
            fsFolder = os.path.join(groupContent, groupID)
            if not os.path.isdir(fsFolder):
                logging.debug(u'No FS export for %s; skipping', groupID)
                continue
            logging.debug(u'Importing %s from FS path %s', groupID, fsFolder)
            groupFolder = groups[groupID]
            _doGroupImport(groupFolder, fsFolder)
            transaction.commit()
    except KeyError:
        logging.warn(u'No "groups" in portal, skipping')
    finally:
        # Finally, make sure everything is indexed so they appear where they need
        # to be
        logging.info('Clearing and rebuilding the catalog')
        catalog = plone.api.portal.get_tool('portal_catalog')
        catalog.clearFindAndRebuild()


def _main(app):
    importDir = os.environ.get('GROUP_EXPORTS')
    if not importDir:
        logging.error(u'Env var GROUP_EXPORTS not set, aborting')
        return False
    importDir = os.path.abspath(importDir)
    app = makerequest.makerequest(app)
    app.REQUEST['PARENTS'] = [app]
    setRequest(app.REQUEST)
    app.REQUEST.traverse('edrn')
    _setupZopeSecurity(app)
    portal = app['edrn']
    setSite(portal)
    _importGroupContent(portal, importDir)
    # For HK:
    catalog = plone.api.portal.get_tool('portal_catalog')
    results = catalog(Title='OC Team Project January 2013 Teleconference Minutes')
    for i in results:
        obj = i.getObject()
        _publish(obj, workflowTool=None, action='retract')
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
