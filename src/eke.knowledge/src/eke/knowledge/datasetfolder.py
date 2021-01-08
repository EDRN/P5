# encoding: utf-8


u'''EKE Knowledge: Dataset Folder'''

from . import _
from .base import Ingestor
from .dataset import IDataset
from .dublincore import TITLE_URI
from .knowledgefolder import IKnowledgeFolder
from .protocol import IProtocol
from Acquisition import aq_inner
from Products.Five import BrowserView
from z3c.relationfield import RelationValue
from zope import schema
from zope.component import getUtility
from zope.interface import implementer
from zope.intid.interfaces import IIntIds
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary
import urlparse, logging, plone.api, rdflib, urllib2, contextlib, json


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
    def getInterfaceForContainedObjects(self, predicates):
        return IDataset
    def getSummaryData(self, source):
        with contextlib.closing(urllib2.urlopen(source)) as bytestring:
            return bytestring.read()
    def ingest(self):
        idUtil = getUtility(IIntIds)
        context = aq_inner(self.context)
        consequences = super(DatasetIngestor, self).ingest()
        catalog = plone.api.portal.get_tool('portal_catalog')

        # First, clear all protocol-to-dataset relations
        for i in catalog(object_provides=IProtocol.__identifier__):
            obj = i.getObject()
            obj.datasets = []

        # Set protocol names & links
        objs = list(consequences.created)
        objs.extend(consequences.updated)
        for datasetObj in objs:
            rv = datasetObj.protocol
            if rv is None or rv.to_object is None: continue
            datasetObj.protocolName = rv.to_object.title
            datasetObj.investigator = rv.to_object.principalInvestigator
            # Why is this extra guard necessary?
            if datasetObj.investigator.to_object is not None and datasetObj.investigator.to_object.title:
                datasetObj.investigatorName = datasetObj.investigator.to_object.title
            if rv.to_object.datasets is None: rv.to_object.datasets = []
            rv.to_object.datasets.append(RelationValue(idUtil.getId(datasetObj)))

        # Add summary data
        if context.dsSumDataSource:
            context.dataSummary = self.getSummaryData(context.dsSumDataSource)
        else:
            context.dataSummary = u'{}'

        portal = plone.api.portal.get()
        catalog.reindexIndex('identifier', portal.REQUEST)
        return consequences
        # Set bodySystemName, protocolName, piNames manually; bodySystemName done


@implementer(IVocabularyFactory)
class BodySystemsInDatasetsVocabulary(object):
    u'''Vocabulary for body systems in datasets'''
    def __call__(self, context):
        catalog = plone.api.portal.get_tool('portal_catalog')
        results = catalog.uniqueValuesFor('bodySystemName')
        vocabs = []
        for i in results:
            if i:
                vocabs.append((i, i))
        vocabs.sort()
        return SimpleVocabulary.fromItems(vocabs)


class DatasetSummary(BrowserView):
    def __call__(self):
        context = aq_inner(self.context)
        self.request.response.setHeader('Content-type', 'application/json; charset=utf-8')
        self.request.response.setHeader('Content-Transfer-Encoding', '8bit')
        if not context.dataSummary:
            return u'{}'
        data = json.loads(context.dataSummary)
        if u'Liver, Placenta, Brain' in data:
            data[u'Liver etc.']  = data[u'Liver, Placenta, Brain']
            del data[u'Liver, Placenta, Brain']
        return json.dumps(data)
