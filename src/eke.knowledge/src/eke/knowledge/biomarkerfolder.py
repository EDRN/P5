# encoding: utf-8

u'''Biomarker folder'''

from . import _
from .base import Ingestor
from .knowledgefolder import IKnowledgeFolder, KnowledgeFolderView
from .site import ISite
from .utils import publish
from Acquisition import aq_inner
from five import grok
from plone.dexterity.utils import createContentInContainer
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.memoize.view import memoize
from zope import schema
from zope.component import getUtility
import urlparse, logging, plone.api, rdflib, dublincore


class IBiomarkerFolder(IKnowledgeFolder):
    u'''Biomarker folder.'''
    bmoDataSource = schema.TextLine(
        title=_(u'Biomarker-Organ RDF Data Source'),
        description=_(u'URL to a source of RDF data that supplements the RDF data source with biomarker-organ data.'),
        required=True
    )
    bmuDataSource = schema.TextLine(
        title=_(u'Biomarker-BioMuta RDF Data Source'),
        description=_(u'URL to a source of RDF data that supplements the RDF data source with biomarker-biomuta data.'),
        required=True
    )
    idDataSource = schema.TextLine(
        title=_(u'Biomarker ID External Resource API Link'),
        description=_(u'URL to a api that allows querying biomarker ids for links and alternative ids of external resources.'),
        required=True
    )
    # dataSummary = schema.TextLine(
    #     title=_(u'Biomarker Statistics'),
    #     description=_(u'Biomarker statistics.'),
    #     required=False
    # )
    disclaimer = schema.Text(
        title=_(u'Disclaimer'),
        description=_(u'Legal disclaimer to display on Biomarker Folder pages.'),
        required=False,
    )


class BiomarkerIngestor(Ingestor):
    grok.context(IBiomarkerFolder)
    def getInterfaceForContainedObjects(self):
        return None
