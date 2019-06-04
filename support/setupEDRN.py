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
import sys, logging, transaction, argparse, os, os.path, plone.api, csv, codecs


logging.basicConfig(level=logging.INFO, format='%(levelname)-8s %(message)s')
app = globals().get('app', None)  # ``app`` comes from ``instance run`` magic.
_argParser = argparse.ArgumentParser(prog='admin.py', description=u'Adds a Manager user')
_argParser.add_argument('username', help=u'Zope admin user')
_argParser.add_argument('password', help=u"Zope admin password")
_argParser.add_argument('ldapPassword', help=u"LDAP password")


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
            <a href='collaborative-groups'>
                Collaborative Groups
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
        <li id='q-committees'>
            <a href='committees'>
                Committees
            </a>
        </li>
        <li id='q-standards'>
            <a href='https://edrn.jpl.nasa.gov/standards/'>
                Biomarker Informatics Standards
            </a>
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
        'checkbox', 'left', 'default',
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
    criteria.add('sorting', 'bottom', 'default', title=u'Sort on', hidden=False, default='sortable_title')
    IFacetedLayout(context).update_layout('faceted_biomarkers_view')


def _setupBiomarkers(context):
    u'''Do extra stuff for biomarkers. Must be defined before _RDF_FOLDERS below.'''
    context.bmoDataSource = u'https://edrn.jpl.nasa.gov/bmdb/rdf/biomarkerorgans?qastate=all'
    context.bmuDataSource = u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/biomuta/@@rdf'
    context.idDataSource = u'https://edrn.jpl.nasa.gov/cancerdataexpo/idsearch'
    context.bmSumDataSource = u'https://edrn.jpl.nasa.gov/cancerdataexpo/summarizer-data/biomarker/@@summary'
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
    criteria.add('sorting', 'bottom', 'default', title=u'Sort on', hidden=False, default='sortable_title')
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
        'checkbox', 'left', 'default',
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
    criteria.add('sorting', 'bottom', 'default', title=u'Sort on', hidden=False, default='sortable_title')
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
    ('resources', 'eke.knowledge.resourcefolder', u'Miscellaneous Resources', u'Various other web-accessible resources.', [u'https://edrn.jpl.nasa.gov/bmdb/rdf/resources'], _null),
    (None, 'eke.knowledge.publicationfolder', u'Publications', u'Items published by EDRN.', [u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/publications/@@rdf', u'http://edrn.jpl.nasa.gov/bmdb/rdf/publications'], _setupPublications),
    (None, 'eke.knowledge.sitefolder', u'Sites', u'Institutions and PIs in EDRN.', [u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/sites/@@rdf'], _setupSites),
    (None, 'eke.knowledge.protocolfolder', u'Protocols', u'Studies pursued by EDRN.', [u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/protocols/@@rdf'], _null),
    (None, 'eke.knowledge.datasetfolder', u'Data', u'Data collected by EDRN.', [u'https://edrn.nci.nih.gov/miscellaneous-knowledge-system-artifacts/science-data-rdf/at_download/file'], _setupDatasets),
    (None, 'eke.knowledge.biomarkerfolder', u'Biomarkers', u'Indicators for cancer.', [u'https://edrn.jpl.nasa.gov/bmdb/rdf/biomarkers?qastate=all'], _setupBiomarkers),
)
# _RDF_FOLDERS = tuple()

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


def _setSiteProposals(portal):
    u'''HK entered this stuff by hand on the old portal.'''
    # Organ or proposal text can be empty strings
    catalog = plone.api.portal.get_tool('portal_catalog')
    with open(os.path.join('data', 'site-hand-info.csv'), 'rb') as f:
        reader = UnicodeReader(f)
        for row in reader:
            identifier, organs, proposal = row
            results = catalog(identifier=identifier, object_provides='eke.knowledge.site.ISite')
            if len(results) == 0:
                logging.info('No sites matching %s found; skipping', identifier)
                continue
            elif len(results) > 1:
                logging.critical('Multiple sites matching %s found (%d); should not happen', results, len(results))
                raise Exception('Multiple sites matching %s found (%d); should not happen' % (results, len(results)))
            else:
                site = results[0].getObject()
                site.organs = organs.split(u',')
                site.proposal = proposal


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
        folder = portal.unrestrictedTraverse(path)
        _addToQuickLinks(folder)

    # Set site proposal
    _setSiteProposals(portal)

    # Finally, make sure everything is indexed so they appear where they need
    # to be
    logging.info('Clearing and rebuilding the catalog')
    catalog = plone.api.portal.get_tool('portal_catalog')
    catalog.clearFindAndRebuild()
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


def _ingest(portal):
    folders, paths, uids = [], [], {}
    for containerPath, fti, title, desc, urls, postFunction in _RDF_FOLDERS:
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
    registry = getUtility(IRegistry)
    registry['eke.knowledge.interfaces.IPanel.objects'] = paths
    ingestor = portal.unrestrictedTraverse('@@ingestRDF')
    ingestor()
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


def _addCollaborativeGroups(portal):
    if 'collaborative-groups' in portal.keys():
        portal.manage_delObjects(['collaborative-groups'])
    folder = createContentInContainer(
        portal, 'Folder', id='collaborative-groups', title=u'Collaborative Groups',
        description=u'Groups that work (and, in fact, collaborate) together.'
    )
    brl = createContentInContainer(
        folder, 'eke.knowledge.groupspacefolder', title=u'Biomarker Reference Laboratories',
        description=u'Biomarker Reference Laboratories Group Pages.'
    )
    breast = createContentInContainer(
        folder, 'eke.knowledge.collaborativegroupfolder', title=u'Breast and Gynecologic Cancers Research Group',
        description=u'Collaborative group for those working on breast and gynecologic cancers.'
    )
    gi = createContentInContainer(
        folder, 'eke.knowledge.collaborativegroupfolder', title=u'G.I. and Other Associated Cancers Research Group',
        description=u'Collaborative group for those working on GI and other associated cancers.'
    )
    lung = createContentInContainer(
        folder, 'eke.knowledge.collaborativegroupfolder', title=u'Lung and Upper Aerodigestive Cancers Research Group',
        description=u'Collaborative group for those working on lung and upper aerodigestive associated cancers.'
    )
    prostate = createContentInContainer(
        folder, 'eke.knowledge.collaborativegroupfolder', title=u'Prostate and Urologic Cancers Research Group',
        description=u'Collaborative group for those working on prostate and urologic cancers.'
    )
    body = _COLLAB_GROUPS_BODY.format(
        brl=brl.UID(), breast=breast.UID(), gi=gi.UID(), lung=lung.UID(), prostate=prostate.UID()
    )
    createContentInContainer(
        folder, 'Document', id='index_html', title=u'Collaborative Groups',
        description=u'Groups that work (and, in fact, collaborate) together.',
        text=RichTextValue(body, 'text/html', 'text/x-html-safe')
    )
    folder.setDefaultPage('index_html')
    _publish(folder)


def _addCommittees(portal):
    if 'committees' in portal.keys():
        portal.manage_delObjects(['committees'])
    folder = createContentInContainer(
        portal, 'Folder', id='committees', title=u'Committees',
        description=u'The following describes the committees, subcommittees, and other components of EDRN.'
    )
    for name in (
        u'Associate Member',
        u'Biomarker Developmental Laboratories',
        u'Biomarker Reference Laboratories',
        u'Clinical Epidemiology and Validation Center',
        u'Collaboration and Publication Subcommittee',
        u'Communication and Workshop Subcommittee',
        u'Data Management and Coordinating Center',
        u'Data Sharing and Informatics Subcommittee',
        u'ERNE Working Group',
        u'Executive Committee',
        u'Jet Propulsion Laboratory',
        u'National Cancer Institute',
        u'Network Consulting Team',
        u'Prioritization Subcommittee',
        u'Steering Committee',
        u'Technology and Resource Sharing Subcommittee'
    ):
        createContentInContainer(folder, 'eke.knowledge.groupspacefolder', title=name)
    _publish(folder)


def _addGroupSpaces(portal):
    u'''Add group workspaces, collaborative groups, committees'''
    _addCollaborativeGroups(portal)
    _addCommittees(portal)


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
    # criteria.add(
    #     'checkbox', 'left', 'default',
    #     title='Organs',
    #     hidden=False,
    #     index='indicatedBodySystems',
    #     operator='or',
    #     vocabulary=u'eke.knowledge.vocabularies.BodySystemsInBiomarkers',
    #     default=[],
    #     count=False,
    #     maxitems=0,
    #     sortreversed=False,
    #     hidezerocount=False
    # )
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
    criteria.add('sorting', 'bottom', 'default', title=u'Sort on', hidden=False, default='sortable_title')
    IFacetedLayout(folder).update_layout('listing_view')
    _publish(folder)


def _setupEDRN(app, username, password, ldapPassword):
    app = makerequest.makerequest(app)
    _setupZopeSecurity(app)
    _nukeAdmins(app)
    _installAdmin(app, username, password)
    portal = _createEDRNSite(app)
    setSite(portal)
    uids = _BLANK_UIDS
    uids.update(_loadZEXPFiles(portal))  # Stack traces; see https://community.plone.org/t/stack-trace-when-loading-zexp-from-a-script/8060
    _setLDAPPassword(portal, ldapPassword)
    uids.update(_ingest(portal))
    _doStaticQuickLinksPortlet(portal, uids)
    _doDMCCRSSPortlet(portal)
    _setGlobalNavOrder(portal)
    _addGroupSpaces(portal)
    _addMembersList(portal)
    _tuneUp(portal)  # this should be the last step always as it clears/rebuids the catalog and commits the txn
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
        _setupEDRN(app, args.username, args.password, args.ldapPassword)
    except Exception as ex:
        logging.exception(u'This is most unfortunate: %s', unicode(ex))
        return False
    return True


if __name__ == '__main__':
    # The [2:] works around plone.recipe.zope2instance-4.2.6's lame bin/interpreter script issue
    sys.exit(0 if main(sys.argv[2:]) is True else -1)
