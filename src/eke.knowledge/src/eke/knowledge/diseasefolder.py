# encoding: utf-8


u'''EKE Knowledge: Disease Folder'''

from .base import Ingestor
from .disease import IDisease
from .knowledgefolder import IKnowledgeFolder


class IDiseaseFolder(IKnowledgeFolder):
    u'''Disease folder.'''


class DiseaseIngestor(Ingestor):
    def getInterfaceForContainedObjects(self, predicates):
        return IDisease
