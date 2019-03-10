# encoding: utf-8


u'''EKE Knowledge: Dataset Folder'''

from .base import Ingestor
from .dublincore import TITLE_URI
from .knowledgefolder import IKnowledgeFolder, KnowledgeFolderView
from .dataset import IDataset
from .site import ISite
from Acquisition import aq_inner
from five import grok
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.memoize.view import memoize
from zope.component import getUtility
import urlparse, logging, plone.api, rdflib


_logger = logging.getLogger(__name__)
_datasetTypeURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/types.rdf#Dataset')
_weirdTitleURI = rdflib.URIRef(u'urn:edrn:DataSetName')


class IDatasetFolder(IKnowledgeFolder):
    u'''Dataset folder.'''


class DatasetIngestor(Ingestor):
    grok.context(IDatasetFolder)
    def getInterfaceForContainedObjects(self):
        return IDataset
    def readRDF(self, url):
        u'''Read the RDF statements and return s/p/o dict'''
        unfiltered, filtered = super(DatasetIngestor, self).readRDF(url), {}
        for subjectURI, predicates in unfiltered.iteritems():
            titles = predicates.get(_weirdTitleURI, [])
            if not titles: continue
            predicates[rdflib.URIRef(TITLE_URI)] = titles
            predicates[rdflib.RDF.type] = [_datasetTypeURI]
            filtered[subjectURI] = predicates
        return filtered
    def ingest(self):
        consequences = super(DatasetIngestor, self).ingest()
        return consequences
        # Set bodySystemName, protocolName, piNames manually
