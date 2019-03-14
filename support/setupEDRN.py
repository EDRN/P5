#!/usr/bin/env python
# encoding: utf-8
# Copyright 2019 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from AccessControl.SecurityManagement import newSecurityManager, noSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy
from eea.facetednavigation.interfaces import ICriteria
from eea.facetednavigation.layout.interfaces import IFacetedLayout
from node.ext.ldap.interfaces import ILDAPProps
from plone.app.dexterity.behaviors.exclfromnav import IExcludeFromNavigation
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer
from plone.registry.interfaces import IRegistry
from Products.CMFCore.interfaces import IFolderish
from Products.CMFCore.tests.base.security import PermissiveSecurityPolicy, OmnipotentUser
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFPlone.factory import addPloneSite
from Testing import makerequest
from zope.component import getUtility, getMultiAdapter
from zope.component.hooks import setSite
import sys, logging, transaction, argparse, os, os.path, plone.api, csv, codecs


logging.basicConfig(level=logging.INFO, format='%(levelname)-8s %(message)s')
app = globals().get('app', None)  # ``app`` comes from ``instance run`` magic.
_argParser = argparse.ArgumentParser(prog='admin.py', description=u'Adds a Manager user')
_argParser.add_argument('username', help=u'Zope admin user')
_argParser.add_argument('password', help=u"Zope admin password")
_argParser.add_argument('ldapPassword', help=u"LDAP password")


_BIOMARKER_DISCLAIMER = u'''<p>The EDRN is involved in researching hundreds of biomarkers. The following is
a partial list of biomarkers and associated results that are currently available for access and viewing.
The bioinformatics team at EDRN is currently working with EDRN collaborative groups to capture, curate,
review, and post the results as it is available. EDRN also provides secure access to additional biomarker
information not available to the public that is currently under review by EDRN research groups. If you have
access to this information, please ensure that you are logged in. If you are unsure or would like access,
please <a href="contact-info">contact the operator</a> for more information.</p>
'''


def _null(context):
    u'''Do noting with the given context object. Must be defined before _RDF_FOLDERS below.'''
    pass


def _setupBiomarkers(context):
    u'''Do extra stuff for biomarkers. Must be defined before _RDF_FOLDERS below.'''
    context.bmoDataSource = u'https://edrn.jpl.nasa.gov/bmdb/rdf/biomarkerorgans?qastate=all'
    context.bmuDataSource = u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/biomuta/@@rdf'
    context.idDataSource = u'https://edrn.jpl.nasa.gov/cancerdataexpo/idsearch'
    context.disclaimer = RichTextValue(_BIOMARKER_DISCLAIMER, 'text/html', 'text/x-html-safe')
    # TODO: Do facets here too


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
    criteria.add('sorting', 'bottom', 'default', title=u'Sort on', hidden=False)
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
    criteria.add('sorting', 'bottom', 'default', title=u'Sort on', hidden=False)
    # Needs debugging
    # IFacetedLayout(context).update_layout('faceted_datasets_view')


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
_PEOPLE_RDF = u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/registered-person/@@rdf'
_RDF_FOLDERS = (
    ('resources', 'eke.knowledge.bodysystemfolder', u'Body Systems', u'Body systems are organs of the body.', [u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/body-systems/@@rdf'], _null),
    ('resources', 'eke.knowledge.diseasefolder', u'Diseases', u'Ailements affecting body systems.', [u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/diseases/@@rdf'], _null),
    (None, 'eke.knowledge.publicationfolder', u'Publications', u'Items published by EDRN.', [u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/publications/@@rdf', u'http://edrn.jpl.nasa.gov/bmdb/rdf/publications'], _applyFacetsToPublications),
    (None, 'eke.knowledge.sitefolder', u'Sites', u'Institutions and PIs in EDRN.', [u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/sites/@@rdf'], _setupSites),
    (None, 'eke.knowledge.protocolfolder', u'Protocols', u'Studies pursued by EDRN.', [u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/protocols/@@rdf'], _null),
    (None, 'eke.knowledge.datasetfolder', u'Science Data', u'Data collected by EDRN.', [u'https://edrn.nci.nih.gov/miscellaneous-knowledge-system-artifacts/science-data-rdf/at_download/file'], _applyFacetsToDatasets),
    # TODO: turned off while I debug other issues
    # (None, 'eke.knowledge.biomarkerfolder', u'Biomarkers', u'Indicators for cancer.', [u'https://edrn.jpl.nasa.gov/bmdb/rdf/biomarkers?qastate=all'], _setupBiomarkers)
)


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
    logging.info('Done importing ZEXP files')
    transaction.commit()


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

    # First, make sure the Network Consulting Team is not in the global navbar
    # but ensure it's on the Quick Links
    if 'network-consulting-team' in portal.keys():
        logging.info('Removing network-consulting-team from navigation')
        folder = portal['network-consulting-team']
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
    folders, paths = [], []
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
    registry = getUtility(IRegistry)
    registry['eke.knowledge.interfaces.IPanel.objects'] = paths
    ingestor = portal.unrestrictedTraverse('@@ingestRDF')
    ingestor()


def _setupEDRN(app, username, password, ldapPassword):
    app = makerequest.makerequest(app)
    _setupZopeSecurity(app)
    _nukeAdmins(app)
    _installAdmin(app, username, password)
    portal = _createEDRNSite(app)
    setSite(portal)
    _loadZEXPFiles(portal)  # Stack traces; see https://community.plone.org/t/stack-trace-when-loading-zexp-from-a-script/8060
    _setLDAPPassword(portal, ldapPassword)
    _ingest(portal)
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
