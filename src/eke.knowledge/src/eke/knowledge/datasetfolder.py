# encoding: utf-8


u'''EKE Knowledge: Dataset Folder'''

from . import _
from .base import Ingestor
from .dataset import IDataset
from .dublincore import TITLE_URI
from .knowledgefolder import IKnowledgeFolder
from Acquisition import aq_inner
from five import grok
from z3c.relationfield import RelationValue
from zope import schema
from zope.component import getUtility
from zope.intid.interfaces import IIntIds
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary
import urlparse, logging, plone.api, rdflib, urllib2, contextlib


_logger = logging.getLogger(__name__)
_datasetTypeURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/types.rdf#Dataset')
_weirdTitleURI = rdflib.URIRef(u'urn:edrn:DataSetName')
_bodySystemPredicateURI = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#organ')


class IDatasetFolder(IKnowledgeFolder):
    u'''Dataset folder.'''
    dsSumDataSource = schema.TextLine(
        title=_(u'Summary Data Source'),
        description=_(u'URL to a source of summary statistics that describes science data for this folder.'),
        required=False,
    )
    dataSummary = schema.Text(
        title=_(u'Data Summary'),
        description=_(u'JSON data that describe summary information for the data in this folder.'),
        required=False,
    )


class DatasetIngestor(Ingestor):
    grok.context(IDatasetFolder)
    def getInterfaceForContainedObjects(self, predicates):
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
    def getSummaryData(self, source):
        with contextlib.closing(urllib2.urlopen(source)) as bytestring:
            return bytestring.read()
    def ingest(self):
        idUtil = getUtility(IIntIds)
        context = aq_inner(self.context)
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
        # Set protocol names & links
        objs = list(consequences.created)
        objs.extend(consequences.updated)
        for datasetObj in objs:
            rv = datasetObj.protocol
            if rv is None or rv.to_object is None: continue
            datasetObj.protocolName = rv.to_object.title
            datasetObj.investigator = rv.to_object.principalInvestigator
            if rv.to_object.datasets is None: rv.to_object.datasets = []
            rv.to_object.datasets.append(RelationValue(idUtil.getId(datasetObj)))
        portal = plone.api.portal.get()
        # Add summary data
        if context.dsSumDataSource:
            context.dataSummary = self.getSummaryData(context.dsSumDataSource)
        else:
            context.dataSummary = u'{}'
        catalog.reindexIndex('identifier', portal.REQUEST)
        return consequences
        # Set bodySystemName, protocolName, piNames manually; bodySystemName done


class BodySystemsInDatasetsVocabulary(object):
    u'''Vocabulary for body systems in datasets'''
    grok.implements(IVocabularyFactory)
    def __call__(self, context):
        catalog = plone.api.portal.get_tool('portal_catalog')
        results = catalog.uniqueValuesFor('bodySystemName')
        vocabs = []
        for i in results:
            if i:
                vocabs.append((i, i))
        vocabs.sort()
        return SimpleVocabulary.fromItems(vocabs)


grok.global_utility(BodySystemsInDatasetsVocabulary, name=u'eke.knowledge.vocabularies.BodySystemsInDatasets')


class DatasetSummary(grok.View):
    grok.context(IDatasetFolder)
    grok.require('zope2.View')
    grok.name('summary')
    def render(self):
        context = aq_inner(self.context)
        self.request.response.setHeader('Content-type', 'application/json; charset=utf-8')
        self.request.response.setHeader('Content-Transfer-Encoding', '8bit')
        return context.dataSummary
