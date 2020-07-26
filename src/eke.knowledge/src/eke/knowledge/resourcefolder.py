# encoding: utf-8


u'''EKE Knowledge: Resources Folder'''

from .base import Ingestor
from .knowledgefolder import IKnowledgeFolder
from .resource import IResource
from plone.i18n.normalizer.interfaces import IIDNormalizer
from zope.component import getUtility
import rdflib


class IResourceFolder(IKnowledgeFolder):
    u'''Resource folder.'''
    pass


class ResourceIngestor(Ingestor):
    def getTitles(self, predicates):
        u'''Get the DC title from ``predicates``. Override this if you need'''
        return predicates.get(rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Description'))
    def getObjID(self, subjectURI, titles, predicates):
        normalize = getUtility(IIDNormalizer).normalize
        return normalize(subjectURI)
    def getInterfaceForContainedObjects(self, predicates):
        return IResource
