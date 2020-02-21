#!/usr/bin/env python
# encoding: utf-8
# Copyright 2019 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from AccessControl.SecurityManagement import newSecurityManager, noSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy
from edrnsite.portlets.portlets.dmccrss import Assignment as DMCCRSSPortletAssignment
from eea.facetednavigation.interfaces import ICriteria
from eea.facetednavigation.layout.interfaces import IFacetedLayout
from node.ext.ldap.interfaces import ILDAPProps
from plone.app.dexterity.behaviors.exclfromnav import IExcludeFromNavigation
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer
from plone.portlet.static.static import Assignment as StaticPortletAssignment
from plone.portlets.interfaces import IPortletManager, IPortletAssignmentMapping
from plone.registry.interfaces import IRegistry
from Products.CMFCore.interfaces import IFolderish
from Products.CMFCore.tests.base.security import PermissiveSecurityPolicy, OmnipotentUser
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFPlone.factory import addPloneSite
from Testing import makerequest
from zope.component import getUtility, getMultiAdapter
from zope.component.hooks import setSite
from zope.container.interfaces import INameChooser
from zope.globalrequest import setRequest
import sys, logging, transaction, argparse, os, os.path, plone.api, getpass


logging.basicConfig(level=logging.INFO, format='%(levelname)-8s %(message)s')
app = globals().get('app', None)  # ``app`` comes from ``instance run`` magic.
_argParser = argparse.ArgumentParser(prog='setupEDRN.py', description=u'Set up P5 EDRN database')
_argParser.add_argument('--username', default='zope', help=u'Zope admin user, defaults to %(default)s')
_argParser.add_argument('--password', default=None, help=u"Zope admin password, prompted if not given")
_argParser.add_argument('--ldapPassword', default=None, help=u"LDAP password, prompted if not given")
_argParser.add_argument('--lightweight', action='store_true', help=u'Make a lite portal, default %(default)s')


_DATASETS_SUMMARY_URL = u'https://edrn.jpl.nasa.gov/cancerdataexpo/summarizer-data/dataset/@@summary'
_PUBLICATIONS_SUMMARY_URL = u'https://edrn.jpl.nasa.gov/cancerdataexpo/summarizer-data/publication/@@summary'

_BIOMARKER_DISCLAIMER = u'''<p>The EDRN is involved in researching hundreds of biomarkers. The following is
a partial list of biomarkers and associated results that are currently available for access and viewing.
The bioinformatics team at EDRN is currently working with EDRN collaborative groups to capture, curate,
review, and post the results as it is available. EDRN also provides secure access to additional biomarker
information not available to the public that is currently under review by EDRN research groups. If you have
access to this information, please ensure that you are logged in. If you are unsure or would like access,
please <a href="mailto:ic-portal@jpl.nasa.gov">contact the operator</a> for more information.</p>
'''
_COLLAB_GROUPS_BODY = u'''<h2>Group Work Spaces</h2>
<ul><li><a href='resolveuid/{brl}'>Biomarker Reference Laboratories</a></li></ul>
<h2>Organ Collaborative Groups</h2>
<ul>
<li><a href='resolveuid/{breast}'>Breast and Gynecologic Cancers Research Group</a></li>
<li><a href='resolveuid/{gi}'>G.I. and Other Associated Cancers Research Group</a></li>
<li><a href='resolveuid/{lung}'>Lung and Upper Aerodigestive Cancers Research Group</a></li>
<li><a href='resolveuid/{prostate}'>Prostate and Urologic Cancers Research Group</a></li>
'''
_QUICKLINKS_BODY = u'''<div class='edrnQuickLinks'>
    <ul id='edrn-quicklinks'>
        <li id='q-nct'>
            <a href='resolveuid/{network-consulting-team}'>
                Network Consulting Team
            </a>
        </li>
        <li id='q-informatics'>
            <a href='resolveuid/{informatics}'>
                Informatics
            </a>
        </li>
        <li id='q-collabGroups'>
            <a href='resolveuid/{groups}'>
                Groups and Committees
            </a>
        </li>
        <li id='q-advocates'>
            <a href='resolveuid/{advocates}'>
                Public, Patients, Advocates
            </a>
        </li>
        <li id='q-fund'>
            <a href='resolveuid/{funding-opportunities}'>
                Funding Opportunities
            </a>
        </li>
        <li id='q-sites'>
            <a href='resolveuid/{sites}'>Sites</a>
        </li>
        <li id='q-members'>
            <a href='members-list'>Member Directory</a>
        </li>
        <li id='q-dcp'>
            <a class='link-plain' href='https://prevention.cancer.gov/'>
                Division of Cancer Prevention
            </a>
        </li>
        <li id='q-cbrg'>
            <a class='link-plain' href='https://prevention.cancer.gov/research-groups/cancer-biomarkers'>
                Cancer Biomarkers Research Group
            </a>
        </li>
        <li id='q-book'>
            <a href='resolveuid/{docs}'>
                Bookshelf
            </a>
        </li>
    </ul>
</div>
'''
_BLANK_UIDS = {
    u'advocates': u'Unknown',
    u'docs': u'Unknown',
    u'funding-opportunities': u'Unknown',
    u'informatics': u'Unknown',
    u'network-consulting-team': u'Unknown',
    u'sites': u'Unknown',
    u'groups': u'Unknown',
}


def _null(context):
    u'''Do noting with the given context object. Must be defined before _RDF_FOLDERS below.'''
    pass


def _applyFacetsToBiomarkers(context):
    u'''Faceted navigation on biomarkers. Must be defined before _RDF_FOLDERS below.'''
    portal = plone.api.portal.get()
    request = portal.REQUEST
    subtyper = getMultiAdapter((context, request), name=u'faceted_subtyper')
    if subtyper.is_faceted or not subtyper.can_enable: return
    subtyper.enable()
    criteria = ICriteria(context)
    for cid in criteria.keys():
        criteria.delete(cid)
    criteria.add('resultsperpage', 'bottom', 'default', title='Results per page', hidden=False, start=0, end=60, step=20,
        default=20)
    criteria.add(
        'checkbox', 'bottom', 'default',
        title='Organs',
        hidden=False,
        index='indicatedBodySystems',
        operator='or',
        vocabulary=u'eke.knowledge.vocabularies.BodySystemsInBiomarkers',
        default=[],
        count=False,
        maxitems=0,
        sortreversed=False,
        hidezerocount=False
    )
    criteria.add(
        'checkbox', 'bottom', 'default',
        title='Portal Type',
        hidden=True,
        index='portal_type',
        operator='or',
        vocabulary=u'eea.faceted.vocabularies.FacetedPortalTypes',
        default=[u'eke.knowledge.elementalbiomarker', u'eke.knowledge.biomarkerpanel'],
        count=False,
        maxitems=0,
        sortreversed=False,
        hidezerocount=False
    )
    criteria.add('text', 'top', 'default', title=u'Search', hidden=False, index='SearchableText',
        wildcard=True, count=False, onlyallelements=True)
    # Shouldn't be hidden but we want better sorting first
    criteria.add('sorting', 'bottom', 'default', title=u'Sort on', hidden=True, default='sortable_title')
    IFacetedLayout(context).update_layout('faceted_biomarkers_view')


def _setupBiomarkers(context):
    u'''Do extra stuff for biomarkers. Must be defined before _RDF_FOLDERS below.'''
    # Disable while BMDB is down:
    # context.bmoDataSource = u'https://edrn.jpl.nasa.gov/bmdb/rdf/biomarkerorgans?qastate=all'
    context.bmoDataSource = u'file:' + os.path.join(os.environ['EDRN_PORTAL_HOME'], u'data', u'bio-organ.rdf')
    context.bmuDataSource = u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/biomuta/@@rdf'
    context.idDataSource = u'https://edrn.jpl.nasa.gov/cancerdataexpo/idsearch'
    # Disable while BMDB is down:
    # context.bmSumDataSource = u'https://edrn.jpl.nasa.gov/cancerdataexpo/summarizer-data/biomarker/@@summary'
    context.bmSumDataSource = u'file:' + os.path.join(os.environ['EDRN_PORTAL_HOME'], u'data', u'bio-summary.json')
    context.disclaimer = RichTextValue(_BIOMARKER_DISCLAIMER, 'text/html', 'text/x-html-safe')
    _applyFacetsToBiomarkers(context)


def _setupSites(context):
    u'''Do extra stuff for sites: people. Must be defined before _RDF_FOLDERS below.'''
    context.peopleDataSources = [_PEOPLE_RDF]


def _applyFacetsToPublications(context):
    u'''Faceted navigation on publications. Must be defined before _RDF_FOLDERS below.'''
    portal = plone.api.portal.get()
    request = portal.REQUEST
    subtyper = getMultiAdapter((context, request), name=u'faceted_subtyper')
    if subtyper.is_faceted or not subtyper.can_enable: return
    subtyper.enable()
    criteria = ICriteria(context)
    for cid in criteria.keys():
        criteria.delete(cid)
    criteria.add('resultsperpage', 'bottom', 'default', title='Results per page', hidden=False, start=0, end=60, step=20,
        default=20)
    criteria.add(
        'checkbox', 'bottom', 'default',
        title='Portal Type',
        hidden=True,
        index='portal_type',
        operator='or',
        vocabulary=u'eea.faceted.vocabularies.FacetedPortalTypes',
        default=[u'eke.knowledge.publication'],
        count=False,
        maxitems=0,
        sortreversed=False,
        hidezerocount=False
    )
    criteria.add('text', 'top', 'default', title=u'Search', hidden=False, index='SearchableText',
        wildcard=True, count=False, onlyallelements=True)
    criteria.add('text', 'top', 'advanced', title=u'Search Titles Only', hidden=False, index='Title', count=False,
        wildcard=True, onlyallelements=True)
    criteria.add('text', 'top', 'advanced', title=u'Authors', hidden=False, index='authors', count=False,
        wildcard=True, onlyallelements=True)
    criteria.add('text', 'top', 'advanced', title=u'Journal', hidden=False, index='journal', count=False,
        wildcard=True, onlyallelements=True)
    criteria.add('text', 'top', 'advanced', title=u'Abstract', hidden=False, index='Description', count=False,
        wildcard=True, onlyallelements=True)
    # Shouldn't be hidden but we want better sorting first
    criteria.add('sorting', 'bottom', 'default', title=u'Sort on', hidden=True, default='sortable_title')
    IFacetedLayout(context).update_layout('faceted_publications_view')


def _applyFacetsToDatasets(context):
    u'''Faceted navigation on datasets. Must be defined before _RDF_FOLDERS below.'''
    portal = plone.api.portal.get()
    request = portal.REQUEST
    subtyper = getMultiAdapter((context, request), name=u'faceted_subtyper')
    if subtyper.is_faceted or not subtyper.can_enable: return
    subtyper.enable()
    criteria = ICriteria(context)
    for cid in criteria.keys():
        criteria.delete(cid)
    criteria.add('resultsperpage', 'bottom', 'default', title='Results per page', hidden=False, start=0, end=60, step=20,
        default=20)
    criteria.add(
        'checkbox', 'bottom', 'default',
        title='Organs',
        hidden=False,
        index='bodySystemName',
        operator='or',
        vocabulary=u'eke.knowledge.vocabularies.BodySystemsInDatasets',
        default=[],
        count=False,
        maxitems=0,
        sortreversed=False,
        hidezerocount=False
    )
    criteria.add(
        'checkbox', 'bottom', 'default',
        title='Portal Type',
        hidden=True,
        index='portal_type',
        operator='or',
        vocabulary=u'eea.faceted.vocabularies.FacetedPortalTypes',
        default=[u'eke.knowledge.dataset'],
        count=False,
        maxitems=0,
        sortreversed=False,
        hidezerocount=False
    )
    criteria.add('text', 'top', 'default', title=u'Search', hidden=False, index='SearchableText',
        wildcard=True, count=False, onlyallelements=True)
    # Shouldn't be hidden but we want better sorting first
    criteria.add('sorting', 'bottom', 'default', title=u'Sort on', hidden=True, default='sortable_title')
    IFacetedLayout(context).update_layout('faceted_datasets_view')


def _setupDatasets(context):
    _applyFacetsToDatasets(context)
    context.dsSumDataSource = _DATASETS_SUMMARY_URL


def _setupPublications(context):
    _applyFacetsToPublications(context)
    context.pubSumDataSource = _PUBLICATIONS_SUMMARY_URL


_EXTENSION_IDS = [
    'plonetheme.barceloneta:default', 'plone.app.caching:default', 'edrnsite.policy:default'
]
_TO_IMPORT = (
    'about-edrn',
    'advocates',
    'beta',
    'cancer-bioinformatics-workshop',
    'c-edrn',
    'colops',
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
_PEOPLE_RDF = u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/registered-person/@@rdf'
_RDF_FOLDERS = (
    ('resources', 'eke.knowledge.bodysystemfolder', u'Body Systems', u'Body systems are organs of the body.', [u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/body-systems/@@rdf'], _null),
    ('resources', 'eke.knowledge.diseasefolder', u'Diseases', u'Ailements affecting body systems.', [u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/diseases/@@rdf'], _null),
    ('resources', 'eke.knowledge.resourcefolder', u'Miscellaneous Resources', u'Various other web-accessible resources.', [u'file:' + os.path.join(os.environ['EDRN_PORTAL_HOME'], u'data', u'bmdb-resources.rdf')], _null),
# Disable while BMDB is down:
#    ('resources', 'eke.knowledge.resourcefolder', u'Miscellaneous Resources', u'Various other web-accessible resources.', [u'https://edrn.jpl.nasa.gov/bmdb/rdf/resources'], _null),
    (None, 'eke.knowledge.publicationfolder', u'Publications', u'Items published by EDRN.', [u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/publications/@@rdf', u'file:' + os.path.join(os.environ['EDRN_PORTAL_HOME'], u'data', u'bmdb-pubs.rdf')], _setupPublications),
# Disable while BMDB is down:
#    (None, 'eke.knowledge.publicationfolder', u'Publications', u'Items published by EDRN.', [u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/publications/@@rdf', u'http://edrn.jpl.nasa.gov/bmdb/rdf/publications'], _setupPublications),
    (None, 'eke.knowledge.sitefolder', u'Sites', u'Institutions and PIs in EDRN.', [u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/sites/@@rdf'], _setupSites),
    (None, 'eke.knowledge.protocolfolder', u'Protocols', u'Studies pursued by EDRN.', [u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/protocols/@@rdf'], _null),
    (None, 'eke.knowledge.datasetfolder', u'Data', u'Data collected by EDRN.', [u'file:' + os.path.join(os.environ['EDRN_PORTAL_HOME'], u'data', u'labcas.rdf')], _setupDatasets),
# Disable while BMDB is down:
#    (None, 'eke.knowledge.biomarkerfolder', u'Biomarkers', u'Indicators for cancer.', [u'https://edrn.jpl.nasa.gov/bmdb/rdf/biomarkers?qastate=all'], _setupBiomarkers),
    (None, 'eke.knowledge.biomarkerfolder', u'Biomarkers', u'Indicators for cancer.', [u'file:' + os.path.join(os.environ['EDRN_PORTAL_HOME'], u'data', u'bio.rdf')], _setupBiomarkers),
    (None, 'eke.knowledge.collaborationsfolder', u'Groups', u'Collaborative Groups and Committees.', [u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/committees/@@rdf'], _null),
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
    return True


def _loadZEXPFiles(portal):
    zexpDir = os.environ.get('ZEXP_EXPORTS', '/usr/local/edrn/portal/zexp-exports')
    uids = {}
    for objID in _TO_IMPORT:
        if objID in portal.keys():
            logging.info('Path "/%s" already exists in portal; skipping zexp import of it', objID)
            obj = portal[objID]
            uids[unicode(objID)] = obj.UID()
            continue
        zexpFile = os.path.join(zexpDir, objID + '.zexp')
        if not os.path.isfile(zexpFile):
            logging.warn('Zexp file "%s" does not exist (or is not a file); skipping import', zexpFile)
            continue
        logging.info('Importing zexp file "%s" to portal path "/%s"', zexpFile, objID)
        portal._importObjectFromFile(zexpFile)
        transaction.commit()
        obj = portal[objID]
        uids[unicode(objID)] = obj.UID()
    logging.info('Done importing ZEXP files')
    transaction.commit()
    return uids


def _addToQuickLinks(context):
    u'''Add the "quicklinks" tag to the given context object.'''
    if u'quicklinks' not in context.subject:
        subjects = list(getattr(context, u'subject', tuple()))
        subjects.append(u'quicklinks')
        context.subject = tuple(subjects)


def _tuneUp(portal):
    u'''Final tweaks.'''

    # First, a couple folders that shouldn't be in global nav but shold be
    # in theQuick Links
    for folderID in ('network-consulting-team', 'sites'):
        if folderID in portal.keys():
            logging.info('Removing %s from navigation', folderID)
            folder = portal[folderID]
            adapter = IExcludeFromNavigation(folder, None)
            if adapter is not None:
                adapter.exclude_from_nav = True
            _addToQuickLinks(folder)

    # Add more items to the Quick Links
    for path in (
        'informatics',
        'advocates',
        'funding-opportunities',
        'docs',
        'administrivia/division-of-cancer-prevention',
        'administrivia/cancer-biomarkers-research-group'
    ):
        try:
            folder = portal.unrestrictedTraverse(path)
            _addToQuickLinks(folder)
        except KeyError:
            pass

    # Clear find rebuild
    logging.info('Clearing and rebuilding the catalog')
    catalog = plone.api.portal.get_tool('portal_catalog')
    catalog.clearFindAndRebuild()

    # Done for now
    transaction.commit()
    return True


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


def _createIngestFolders(portal, rdfFolders, lightweight):
    folders, paths, uids = [], [], {}
    for containerPath, fti, title, desc, urls, postFunction in rdfFolders:
        if containerPath is None:
            container = portal
        else:
            container = portal.unrestrictedTraverse(containerPath)
        folder = createContentInContainer(
            container,
            fti,
            title=title,
            description=desc,
            rdfDataSources=urls,
            ingestEnabled=True
        )
        postFunction(folder)
        folders.append(folder)
        if containerPath is None:
            paths.append(unicode(folder.id))
        else:
            paths.append(unicode(containerPath + '/' + folder.id))
    for f in folders:
        _publish(f)
        uids[f.id] = f.UID()
    if not lightweight:
        # In non-lightweight mode, an ingest step could populate the database with huge
        # amounts of content, which would make it decidedly non-lightweight.  So we set
        # the ingest paths only in heavy mode (not lightweight).
        registry = getUtility(IRegistry)
        registry['eke.knowledge.interfaces.IPanel.objects'] = paths

        # The paths normally include:
        # resources/body-systems
        # resources/diseases
        # resources/miscellaneous-resources
        # publications
        # sites
        # protocols
        # data
        # biomarkers
        # groups

    return uids


def _doStaticQuickLinksPortlet(portal, uids):
    body = _QUICKLINKS_BODY.format(**uids)
    assignment = StaticPortletAssignment(
        header=u'Quick Links',
        text=RichTextValue(body, 'text/html', 'text/html'),
        omit_border=False
    )
    manager = getUtility(IPortletManager, u'plone.leftcolumn')
    mapping = getMultiAdapter((portal, manager), IPortletAssignmentMapping)
    chooser = INameChooser(mapping)
    mapping[chooser.chooseName(None, assignment)] = assignment


def _doDMCCRSSPortlet(portal):
    frontPage = portal.get('front-page')
    if frontPage is None: return
    assignment = DMCCRSSPortletAssignment()
    manager = getUtility(IPortletManager, u'plone.rightcolumn')
    mapping = getMultiAdapter((frontPage, manager), IPortletAssignmentMapping)
    chooser = INameChooser(mapping)
    mapping[chooser.chooseName(None, assignment)] = assignment


def _setGlobalNavOrder(portal):
    u'''Set the order of global navigation'''
    portal = plone.api.portal.get()
    # Change order per  HK email 3F252A07-9FC1-47AB-A29A-DAF3A6A1B141@jpl.nasa.gov:
    items = ['biomarkers', 'protocols', 'data', 'publications', 'resources', 'about-edrn']
    items.reverse()
    for item in items:
        if item in portal.keys():
            portal.moveObjectsToTop([item])


def _addMembersList(portal):
    u'''Add the faceted members list'''
    if 'members-list' in portal.keys():
        portal.manage_delObjects(['members-list'])
    folder = createContentInContainer(
        portal, 'Folder', id='members-list', title=u'Members List',
        description=u'A directory of the people that comprise EDRN.'
    )
    adapter = IExcludeFromNavigation(folder, None)
    if adapter is not None:
        adapter.exclude_from_nav = True
    subtyper = getMultiAdapter((folder, portal.REQUEST), name=u'faceted_subtyper')
    if subtyper.is_faceted or not subtyper.can_enable: return
    subtyper.enable()
    criteria = ICriteria(folder)
    for cid in criteria.keys():
        criteria.delete(cid)
    criteria.add('resultsperpage', 'bottom', 'default', title='Results per page', hidden=False, start=0, end=60, step=20,
        default=20)
    criteria.add(
        'checkbox', 'bottom', 'default',
        title=u'Investigator',
        hidden=False,
        index='piName',
        operator='or',
        vocabulary=u'eke.knowledge.vocabularies.PrincipalInvestigators',
        count=False,
        maxitems=4,
        sortreversed=False,
        hidezerocount=False
    )
    criteria.add(
        'checkbox', 'bottom', 'default',
        title=u'Institution',
        hidden=False,
        index='siteName',
        operator='or',
        vocabulary=u'eke.knowledge.vocabularies.SiteNames',
        count=False,
        maxitems=4,
        sortreversed=False,
        hidezerocount=False
    )
    criteria.add(
        'checkbox', 'bottom', 'default',
        title=u'Member Type',
        hidden=False,
        index='memberType',
        operator='or',
        vocabulary=u'eke.knowledge.vocabularies.MemberTypes',
        count=False,
        maxitems=4,
        sortreversed=False,
        hidezerocount=False
    )
    criteria.add(
        'checkbox', 'bottom', 'default',
        title='Portal Type',
        hidden=True,
        index='portal_type',
        operator='or',
        vocabulary=u'eea.faceted.vocabularies.FacetedPortalTypes',
        default=[u'eke.knowledge.person'],
        count=False,
        maxitems=0,
        sortreversed=False,
        hidezerocount=False
    )
    # Shouldn't be hidden but we want better sorting first
    criteria.add('sorting', 'bottom', 'default', title=u'Sort on', hidden=True, default='sortable_title')
    IFacetedLayout(folder).update_layout('listing_view')
    _publish(folder)


def _empowerSuperUsers(portal):
    groupsTool = plone.api.portal.get_tool('portal_groups')
    groupsTool.editGroup('Super User', roles=['Manager'], groups=())
    groupsTool.editGroup('Portal Content Custodian', roles=['Site Administrator'], groups=())


def _setupEDRN(app, username, password, ldapPassword, rdfFolders, lightweight):
    app = makerequest.makerequest(app)
    app.REQUEST['PARENTS'] = [app]
    setRequest(app.REQUEST)
    _setupZopeSecurity(app)
    _nukeAdmins(app)
    _installAdmin(app, username, password)
    portal = _createEDRNSite(app)
    setSite(portal)
    uids = _BLANK_UIDS
    if not lightweight:
        # Stack traces; see https://community.plone.org/t/stack-trace-when-loading-zexp-from-a-script/8060
        uids.update(_loadZEXPFiles(portal))
    _setLDAPPassword(portal, ldapPassword)
    uids.update(_createIngestFolders(portal, rdfFolders, lightweight))  # this used to ingest as well, but reasons
    _doStaticQuickLinksPortlet(portal, uids)
    _doDMCCRSSPortlet(portal)
    _setGlobalNavOrder(portal)
    _addMembersList(portal)
    _empowerSuperUsers(portal)
    # We used to clear/rebuild the catalog here but ingest is moved to a separate step for reasons.
    # That means some other step must clear/rebuild the catalog in order to get a database in good
    # working order.
    _tuneUp(portal)
    noSecurityManager()


def main(argv):
    _setupLogging()
    try:
        installDir = os.environ.get('EDRN_PORTAL_HOME')
        if not installDir:
            raise Exception('The EDRN_PORTAL_HOME environment variable is not set')
        os.chdir(installDir)
        global app
        args = _argParser.parse_args(argv[1:])
        username = args.username
        password = args.password if args.password else getpass.getpass(u'Password for Zope user "{}": '.format(username))
        ldapPassword = args.ldapPassword if args.ldapPassword else getpass.getpass(u'LDAP password: ')
        rdfFolders = tuple() if args.lightweight else _RDF_FOLDERS
        _setupEDRN(app, username, password, ldapPassword, rdfFolders, args.lightweight)
    except Exception as ex:
        logging.exception(u'This is most unfortunate: %s', unicode(ex))
        return False
    return True


if __name__ == '__main__':
    # The [2:] works around plone.recipe.zope2instance-4.2.6's lame bin/interpreter script issue
    sys.exit(0 if main(sys.argv[2:]) is True else -1)
