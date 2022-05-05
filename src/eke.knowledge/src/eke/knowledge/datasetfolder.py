# encoding: utf-8


u'''EKE Knowledge: Dataset Folder'''

from . import _
from .base import Ingestor
from .dataset import IDataset
from .knowledgefolder import IKnowledgeFolder
from .protocol import IProtocol
from .utils import publish, retract
from Acquisition import aq_inner
from Products.Five import BrowserView
from z3c.relationfield import RelationValue
from zope import schema
from zope.component import getUtility, getMultiAdapter
from zope.interface import implementer
from zope.intid.interfaces import IIntIds
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary
import logging, plone.api, rdflib, urllib2, contextlib, json, subprocess


_logger = logging.getLogger(__name__)
_datasetTypeURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/types.rdf#Dataset')
_weirdTitleURI = rdflib.URIRef(u'urn:edrn:DataSetName')
_bodySystemPredicateURI = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#organ')
_cardinalityPredicateURI = rdflib.URIRef('urn:edrn:predicates:cardinality')
_collectionsContainerURI = rdflib.URIRef('https://edrn-labcas.jpl.nasa.gov/data-access-api/collections')
_datasetsContainerURI = rdflib.URIRef('https://edrn-labcas.jpl.nasa.gov/data-access-api/datasets')
_filesContainerURI = rdflib.URIRef('https://edrn-labcas.jpl.nasa.gov/data-access-api/files')


# These programs might work to generate images for us
_programs = ['chromium-browser', 'chromium', 'google-chrome']


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
    showStatistics = schema.Bool(
        title=_(u'Show Statistics'),
        description=_(u'If checked, create and show the statistical graphics.'),
        required=False,
        default=True
    )
    statisticsPage = schema.TextLine(
        title=_(u'Statistics Page'),
        description=_(u'URL to a page that contains statistics to show'),
        required=False,
        default=u'https://edrn-labcas.jpl.nasa.gov/labcas-ui/a/index.html'
    )
    virtualTimeBudget = schema.Int(
        title=_(u'Vitual Time Budget'),
        description=_(u'How long to allocate for the rendering of graphics in milliseconds.'),
        required=False,
        default=10000
    )
    windowSize = schema.TextLine(
        title=_(u'Virtual Browser Size'),
        description=_(u'Size of the virtual browser window in pixels: width,height.'),
        required=False,
        default=u'1280,500'
    )
    crop = schema.TextLine(
        title=_(u'Crop Area'),
        description=_(u'Section of the virtual browser to crop for the desired image, ul-x,ul-y,lr-x,lr-y'),
        required=False,
        default=u'50,10,1200,200'
    )
    scale = schema.Float(
        title=_(u'Scale'),
        description=_(u'How much to scale the desired image, as a floating point value.'),
        required=False,
        default=1.0
    )
    numberCollections = schema.Int(
        title=_(u'Collections'),
        description=_(u'The number of collections in LabCAS.'),
        required=False,
        default=36
    )
    numberDatasets = schema.Int(
        title=_(u'Datasets'),
        description=_(u'The number of datasets in LabCAS'),
        required=False,
        default=8532
    )
    numberFiles = schema.Int(
        title=_(u'Files'),
        description=_(u'The number of files in LabCAS'),
        required=False,
        default=172059
    )


# class DatasetFolderView(BrowserView):
#     # Testing methods used to figure stuff out
#     def disciplineByCollectionAbscissa(self):
#         return json.dumps([1, 3, 5])
#     def disciplineByCollectionOrdinate(self):
#         return json.dumps(['alpha', 'beta', 'gamma'])


class DatasetIngestor(Ingestor):

    # For future use, consider running a browser from the portal to render graphics that
    # are just too hard to do in Plone:
    # chromium-browser --disable-software-rasterizer --run-all-compositor-stages-before-draw \
    # --virtual-time-budget=10000 --window-size=1280,500 --no-sandbox --headless --screenshot \
    #  https://edrn-labcas.jpl.nasa.gov/labcas-ui/a/index.html

    _publicGroup = 'All Users'

    def getInterfaceForContainedObjects(self, predicates):
        return IDataset

    def getSummaryData(self, source):
        with contextlib.closing(urllib2.urlopen(source)) as bytestring:
            return bytestring.read()

    def generateImage(self, url, budget, size):
        # I'm not in love with the way this works, so I'm not even going to bother to
        # implement it for now. Besides the milestone deadline for 5.1.0 passed last year.
        try:
            return None
        except subprocess.CalledProcessError as ex:  # noqa
            # Note on macOS, this always fails
            return None

    def _getCardinality(self, statements, subject):
        '''Get the cardinality predicate for ``subject`` from the given ``statements`` as an integer
        or None if it's not there or unparseable.
        '''
        try:
            return int(statements[subject][_cardinalityPredicateURI][0])
        except (KeyError, IndexError, ValueError):
            return None

    def updateStatistics(self, statements):
        context = aq_inner(self.context)

        # First the overall stats
        collections = self._getCardinality(statements, _collectionsContainerURI)
        datasets    = self._getCardinality(statements, _datasetsContainerURI)
        files       = self._getCardinality(statements, _filesContainerURI)

        if collections is not None:
            context.numberCollections = collections
        if datasets is not None:
            context.numberDatasets = datasets
        if files is not None:
            context.numberFiles = files

        # Now the graphics generation
        if not context.showStatistics: return
        imageData = self.generateImage(context.statisticsPage, context.virtualTimeBudget, context.windowSize)
        if imageData is None: return

    def ingest(self):
        idUtil = getUtility(IIntIds)
        context = aq_inner(self.context)
        consequences = super(DatasetIngestor, self).ingest()
        request = plone.api.portal.get().REQUEST
        self.updateStatistics(consequences.statements)

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

            # And set permissions, etc.
            if datasetObj.accessGroups is None:
                datasetObj.accessGroups = []
            groupNames = set([i.split(',')[0][3:] for i in datasetObj.accessGroups])
            if self._publicGroup in groupNames:
                publish(datasetObj)
            else:
                retract(datasetObj)
            sharing = getMultiAdapter((datasetObj, request), name=u'sharing')
            settings = [dict(type='group', roles=[u'Reader'], id=i) for i in groupNames]
            sharing.update_role_settings(settings)

        # Add summary data (soon to be unusued)
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
            data[u'Liver etc.'] = data[u'Liver, Placenta, Brain']
            del data[u'Liver, Placenta, Brain']
        return json.dumps(data)
