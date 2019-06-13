# encoding: utf-8


u'''EKE Knowledge: Collaborations Folder'''


from .base import Ingestor
from .collaborativegroupfolder import ICollaborativeGroupFolder
from .groupspacefolder import IGroupSpaceFolder
from .knowledgefolder import IKnowledgeFolder, KnowledgeFolderView
from Acquisition import aq_inner
from eke.knowledge import _
from five import grok
from plone.memoize.view import memoize
from zope import schema
import rdflib, plone.api

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


class ICollaborationsFolderIngestor(Ingestor):
    grok.context(ICollaborationsFolder)
    def getInterfaceForContainedObjects(self, predicates):
        committeeType = unicode(predicates.get(_committeeTypePredicateURI, [u'Unknown'])[0])
        return ICollaborativeGroupFolder if committeeType == u'Collaborative Group' else IGroupSpaceFolder


class View(KnowledgeFolderView):
    grok.context(ICollaborationsFolder)
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
