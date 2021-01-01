# encoding: utf-8


u'''EKE Knowledge: Collaborations Folder'''


from . import _
from .base import Ingestor
from .biomarker import IBiomarker
from .collaborativegroupfolder import ICollaborativeGroupFolder
from .dataset import IDataset
from .groupspacefolder import IGroupSpaceFolder
from .knowledgefolder import IKnowledgeFolder, KnowledgeFolderView
from .protocol import IProtocol
from Acquisition import aq_inner
from eke.knowledge.collaborativegroupindex import ICollaborativeGroupIndex
from plone.memoize.view import memoize
from z3c.relationfield import RelationValue
from zope import schema
from zope.component import getUtility
from zope.intid.interfaces import IIntIds
import rdflib, plone.api, logging


_logger = logging.getLogger(__name__)
_committeeTypePredicateURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#committeeType')


class ICollaborationsFolder(IKnowledgeFolder):
    u'''Collaborations folder.'''
    title = schema.TextLine(
        title=_(u'Title'),
        description=_(u'Descriptive name of this folder.'),
        required=True,
    )
    description = schema.Text(
        title=_(u'Description'),
        description=_(u'A short summary of this folder.'),
        required=False,
    )


class CollaborationsFolderIngestor(Ingestor):
    def getInterfaceForContainedObjects(self, predicates):
        committeeType = unicode(predicates.get(_committeeTypePredicateURI, [u'Unknown'])[0])
        return ICollaborativeGroupFolder if committeeType == u'Collaborative Group' else IGroupSpaceFolder
    def _setRelations(self, groupIndex, attributeName, interface, correspondingNames, **criteria):
        catalog, idUtil = plone.api.portal.get_tool('portal_catalog'), getUtility(IIntIds)
        results = catalog(
            object_provides=interface.__identifier__,
            collaborativeGroup=correspondingNames,
            sort_on='sortable_title',
            **criteria
        )
        setattr(groupIndex, attributeName, [RelationValue(idUtil.getId(i.getObject())) for i in results])
    def setDatasets(self, groupIndex):
        # https://github.com/EDRN/P5/issues/90 — no need for this anymore:
        #     correspondingDatasetGroupName = _datasetGroupNameMapping.get(groupIndex.title.strip())
        #     if not correspondingDatasetGroupName: return
        # We can now use our group name directly:
        self._setRelations(groupIndex, 'datasets', IDataset, [groupIndex.title.strip()])
    def setBiomarkers(self, groupIndex):
        self._setRelations(groupIndex, 'biomarkers', IBiomarker, [groupIndex.title.strip()])
    def setProtocols(self, groupIndex):
        self._setRelations(groupIndex, 'protocols', IProtocol, [groupIndex.title.strip()], project=False)
    def setProjects(self, groupIndex):
        self._setRelations(groupIndex, 'projects', IProtocol, [groupIndex.title.strip()], project=True)
    def ingest(self):
        consequences = super(CollaborationsFolderIngestor, self).ingest()
        # See if this helps with initial ingest from setupEDRN.py
        catalog = plone.api.portal.get_tool('portal_catalog')
        catalog.manage_reindexIndex(['object_provides', 'collaborativeGroup', 'project'])
        # Now do things normally
        context = aq_inner(self.context)
        for i in context.restrictedTraverse('@@contentlisting')():
            groupFolder = i.getObject()
            if 'index_html' not in groupFolder.keys():
                _logger.info(u'Collaborative group at %s has no index object named "index_html"; skipping', i.getPath())
                continue
            index = groupFolder['index_html']
            if not ICollaborativeGroupIndex.providedBy(index): continue
            self.setDatasets(index)
            self.setBiomarkers(index)
            self.setProtocols(index)
            self.setProjects(index)
        return consequences


class View(KnowledgeFolderView):
    def _contents(self, portal_type):
        context = aq_inner(self.context)
        catalog = plone.api.portal.get_tool('portal_catalog')
        return catalog(
            portal_type=portal_type,
            path=dict(query='/'.join(context.getPhysicalPath()), depth=1),
            sort_on='sortable_title'
        )
    @memoize
    def committees(self):
        return self._contents('eke.knowledge.groupspacefolder')
    @memoize
    def collaborativeGroups(self):
        return self._contents('eke.knowledge.collaborativegroupfolder')
