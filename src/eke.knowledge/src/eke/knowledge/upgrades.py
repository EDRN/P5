#-*- coding: utf-8 -*-


from . import PACKAGE_NAME
from .knowledgeobject import IKnowledgeObject
from .biomarker import IPhasedObject, IBiomarker
from .utils import publish
from eea.facetednavigation.interfaces import ICriteria
from eea.facetednavigation.layout.interfaces import IFacetedLayout
from plone.app.dexterity.behaviors.exclfromnav import IExcludeFromNavigation
from plone.dexterity.utils import createContentInContainer
from zope.component import getMultiAdapter
from Acquisition import aq_parent
import logging, plone.api


PROFILE = 'profile-' + PACKAGE_NAME + ':default'


def reloadTypes(setupTool, logger=None):
    if logger is None:
        logger = logging.getLogger(PACKAGE_NAME)
    logger.info(u'Reloading content types')
    setupTool.runImportStepFromProfile(PROFILE, 'typeinfo')


def reloadCatalog(setupTool, logger=None):
    if logger is None:
        logger = logging.getLogger(PACKAGE_NAME)
    logger.info(u'Reloading catalog')
    setupTool.runImportStepFromProfile(PROFILE, 'catalog')


def stupidPhases(setupTool, logger=None):
    # For https://github.com/EDRN/P5/issues/105
    _phases = {
        u'One': u'1',
        u'Two': u'2',
        u'Three': u'3',
        u'Four': u'4',
        u'Five': u'5'
    }
    if logger is None:
        logger = logging.getLogger(PACKAGE_NAME)
    catalog = plone.api.portal.get_tool('portal_catalog')
    results = catalog(object_provides=IBiomarker.__identifier__)
    for i in results:
        obj = i.getObject()
        obj.phases = []
    results = catalog(object_provides=IPhasedObject.__identifier__)
    for i in results:
        obj = i.getObject()
        newPhase = _phases.get(obj.phase)
        if newPhase is not None:
            obj.phase = newPhase
            biomarker = aq_parent(obj)
            currentPhases = set(biomarker.phases)
            currentPhases.add(newPhase)
            biomarker.phases = list(currentPhases)
            biomarker.reindexObject(idxs=['phases'])


def reindexSearchableTextForKnowledgeObjects(setupTool, logger=None):
    # For https://github.com/EDRN/P5/issues/32
    if logger is None:
        logger = logging.getLogger(PACKAGE_NAME)
    logger.info(u'Re-indexing the catalog')
    catalog = plone.api.portal.get_tool('portal_catalog')
    # This takes FOREVER:
    # catalog.refreshCatalog(clear=1)  # Do we need clear=1?
    # Maybe this'll be faster? We just added text indexing to the title attribute after all:
    results = catalog(object_provides=IKnowledgeObject.__identifier__)
    for i in results:
        i.getObject().reindexObject(idxs=['SearchableText'])


def publishDiseaseFolders(setupTool, logger=None):
    # For https://github.com/EDRN/P5/issues/30
    if logger is None:
        logger = logging.getLogger(PACKAGE_NAME)
    portal = plone.api.portal.get()
    try:
        df = portal.unrestrictedTraverse('resources/diseases')
        logger.info('Publishing disease folder %r', df)
        publish(df)
    except KeyError:
        logger.warn('No diseases folder found under resources, so cannot publish it; skipping')


def addPhaseFacet(setupTool, logger=None):
    # For https://github.com/EDRN/P5/issues/105
    if logger is None:
        logger = logging.getLogger(PACKAGE_NAME)
    portal = plone.api.portal.get()
    if 'biomarkers' not in portal.keys():
        logger.info(u'No biomarkers folder found, so not altering any facets')
        return
    biomarkers = portal['biomarkers']
    subtyper = getMultiAdapter((biomarkers, portal.REQUEST), name=u'faceted_subtyper')
    if not subtyper.is_faceted and not subtyper.can_enable:
        logger.info(u'The biomarkers folder is not faceted and cannot *be* faceted, so not doing anything with it')
        return
    criteria = ICriteria(biomarkers)
    criteria.add(
        'checkbox', 'bottom', 'default',
        title=u'Phase',
        hidden=False,
        index='phases',
        operator='or',
        vocabulary=u'eke.knowledge.vocabularies.Phases',
        count=False,
        maxitems=6,
        sortreversed=False,
        hidezerocount=False
    )


def changeFacets(setupTool, logger=None):
    # For https://github.com/EDRN/P5/issues/23
    if logger is None:
        logger = logging.getLogger(PACKAGE_NAME)
    portal = plone.api.portal.get()
    if 'members-list' in portal:
        portal.manage_delObjects(['members-list'])
    members = createContentInContainer(
        portal, 'Folder', id='members-list', title=u'Members List',
        description=u'A directory of the people that comprise EDRN.'
    )
    request, adapter = portal.REQUEST, IExcludeFromNavigation(members, None)
    if adapter is not None:
        adapter.exclude_from_nav = True
    subtyper = getMultiAdapter((members, request), name=u'faceted_subtyper')
    if subtyper.is_faceted or not subtyper.can_enable: return
    subtyper.enable()
    criteria = ICriteria(members)
    for cid in criteria.keys(): criteria.delete(cid)
    criteria.add(
        'resultsperpage', 'bottom', 'default', title='Results per page', hidden=False,
        start=0, end=60, step=5, default=10
    )
    criteria.add(
        'text', 'top', 'default',
        title=u'Search',
        hidden=False,
        index='SearchableText',
        wildcard=True,
        count=False,
        onlyallelements=True
    )
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
    IFacetedLayout(members).update_layout('faceted_members_view')
    publish(members)


def addGrantNumbers(setupTool, logger=None):
    if logger is None:
        logger = logging.getLogger(PACKAGE_NAME)
    portal = plone.api.portal.get()
    if 'publications' not in portal.keys():
        logger.warn(u'No publications folder in the root of the portal, so no upgrading it with grant numbers')
        return
    publications = portal['publications']
    publications.grantNumbers = [
        u'CA086368',
        u'CA086400',
        u'CA113913',
        u'CA115091',
        u'CA115102',
        u'CA152637',
        u'CA152653',
        u'CA152662',
        u'CA152753',
        u'CA152756',
        u'CA152813',
        u'CA152990',
        u'CA200462',
        u'CA200464',
        u'CA200469',
        u'CA200495',
        u'CA214165',
        u'CA214170',
        u'CA214172',
        u'CA214182',
        u'CA214183',
        u'CA214194',
        u'CA214195',
        u'CA214201'
    ]
    num = len(publications.grantNumbers)
    logger.info(u'Added %d grant numbers to the publications folder; now you just have to do an ingest', num)


def redoBodySystemNames(setupTool, logger=None):
    if logger is None:
        logger = logging.getLogger(PACKAGE_NAME)
    logger.info(u'🤪 Redoing «bodySystemName» index')

    catalog = plone.api.portal.get_tool('portal_catalog')
    catalog.delColumn('bodySystemName')
    catalog.delIndex('bodySystemName')
    catalog.addIndex('bodySystemName', 'KeywordIndex')
    catalog.addColumn('bodySystemName')

    portal = plone.api.portal.get()
    try:
        dataFolder = portal.unrestrictedTraverse('data')
        for objID, obj in dataFolder.items():
            organs = obj.bodySystemName
            if organs:
                organs = organs.split(', ')
                obj.bodySystemName = organs
                obj.reindexObject(idxs=['bodySystemName'])
    except KeyError:
        logger.warn('🧐 No data folder found, skipping transforming organ names on data')


def fixRDFURLs(setupTool, logger=None):
    if logger is None:
        logger = logging.getLogger(PACKAGE_NAME)
    logger.info(u'Fixing some temp ingest paths')
    portal = plone.api.portal.get()
    try:
        siteFolder = portal.unrestrictedTraverse('sites')
        siteFolder.rdfDataSources = ['https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/sites/@@rdf']
        siteFolder.peopleDataSources = ['https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/registered-person/@@rdf']
    except KeyError:
        logger.warn('🧐 No sites folder found, not fixing its RDF source URLs')
    try:
        dataFolder = portal.unrestrictedTraverse('data')
        dataFolder.dsSumDataSource = 'https://edrn.jpl.nasa.gov/cancerdataexpo/static-sources/dataset-summary.json/@@download/file/dataset-summary.json'
    except KeyError:
        logger.warn('🧐 No data folder found, not fixing its summary source URL')
    try:
        biomarkerFolder = portal.unrestrictedTraverse('biomarkers')
        biomarkerFolder.bmSumDataSource = 'https://edrn.jpl.nasa.gov/cancerdataexpo/summarizer-data/biomarker/@@summary'
    except KeyError:
        logger.warn('🧐 No biomarkers folder found, not fixing its summary source URL')


# Commented-out from auto-generated code in case we need it some day:
# from plone.app.upgrade.utils import loadMigrationProfile
# def reload_gs_profile(context):
#     loadMigrationProfile(
#         context,
#         'profile-eke.knowledge:default',
#     )
