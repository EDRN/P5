# -*- coding: utf-8 -*-


from . import PACKAGE_NAME
from .diseasefolder import IDiseaseFolder
from .knowledgeobject import IKnowledgeObject
from .utils import publish
from eea.facetednavigation.interfaces import ICriteria
from eea.facetednavigation.layout.interfaces import IFacetedLayout
from plone.app.dexterity.behaviors.exclfromnav import IExcludeFromNavigation
from plone.dexterity.utils import createContentInContainer
from zope.component import getMultiAdapter
import logging, plone.api


PROFILE = 'profile-' + PACKAGE_NAME + ':default'


def reloadTypes(setupTool, logger=None):
    if logger is None:
        logger = logging.getLogger(PACKAGE_NAME)
    logger.info(u'Reloading content types')
    setupTool.runImportStepFromProfile(PROFILE, 'typeinfo')


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
    catalog = plone.api.portal.get_tool('portal_catalog')
    results = catalog(object_provides=IDiseaseFolder.__identifier__)
    for i in results:
        publish(i.getObject())


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


# Commented-out from auto-generated code in case we need it some day:
# from plone.app.upgrade.utils import loadMigrationProfile
# def reload_gs_profile(context):
#     loadMigrationProfile(
#         context,
#         'profile-eke.knowledge:default',
#     )
