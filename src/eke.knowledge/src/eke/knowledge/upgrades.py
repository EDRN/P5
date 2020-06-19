# -*- coding: utf-8 -*-


from . import PACKAGE_NAME
from .knowledgeobject import IKnowledgeObject
from .diseasefolder import IDiseaseFolder
from .utils import publish
import logging, plone.api

PROFILE = 'profile-' + PACKAGE_NAME + ':default'


def reindexSearchableTextForKnowledgeObjects(setupTool, logger=None):
    # For https://github.com/EDRN/P5/issues/32
    if logger is None:
        logger = logging.getLogger(PACKAGE_NAME)
    logger.info('📚 Re-indexing the catalog')
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


# Commented-out from auto-generated code in case we need it some day:
# from plone.app.upgrade.utils import loadMigrationProfile
# def reload_gs_profile(context):
#     loadMigrationProfile(
#         context,
#         'profile-eke.knowledge:default',
#     )
