# encoding: utf-8


u'''EKE Knowledge: Dataset Folder'''

from .base import Ingestor
from .dataset import IDataset
from .dublincore import TITLE_URI
from .knowledgefolder import IKnowledgeFolder, KnowledgeFolderView
from Acquisition import aq_inner
from five import grok
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.memoize.view import memoize
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary
import urlparse, logging, plone.api, rdflib


_logger = logging.getLogger(__name__)
_datasetTypeURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/types.rdf#Dataset')
_weirdTitleURI = rdflib.URIRef(u'urn:edrn:DataSetName')
_bodySystemPredicateURI = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#organ')


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
        catalog = plone.api.portal.get_tool('portal_catalog')
        for uri, predicates in consequences.statements.iteritems():
            if _bodySystemPredicateURI in predicates:
                results = catalog(identifier=unicode(uri), object_provides=IDataset.__identifier__)
                if len(results) == 1:
                    dataset = results[0].getObject()
                    # eCAS doesn't use valid URIs to body systems so we manually extract them
                    organ = urlparse.urlparse(unicode(predicates[_bodySystemPredicateURI][0]))[2].split('/')[-1]
                    dataset.bodySystemName = organ
        portal = plone.api.portal.get()
        catalog.reindexIndex('identifier', portal.REQUEST)
        return consequences
        # Set bodySystemName, protocolName, piNames manually; bodySystemName done


class IndicatedBodySystemsVocabulary(object):
    u'''Vocabulary for body systems in datasets'''
    grok.implements(IVocabularyFactory)
    def __call__(self, context):
        catalog = plone.api.portal.get_tool('portal_catalog')
        results = catalog.uniqueValuesFor('bodySystemName')
        vocabs = []
        for i in results:
            if i:
                vocabs.append((i, i))
        return SimpleVocabulary.fromItems(vocabs)


grok.global_utility(IndicatedBodySystemsVocabulary, name=u'eke.knowledge.vocabularies.IndicatedBodySystems')
