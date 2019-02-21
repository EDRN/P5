# encoding: utf-8


u'''EKE Knowledge: Disease Folder'''

from .base import Ingestor
from .disease import IDisease
from .knowledgefolder import IKnowledgeFolder
from five import grok


class IDiseaseFolder(IKnowledgeFolder):
    u'''Disease folder.'''


class DiseaseIngestor(Ingestor):
    grok.context(IDiseaseFolder)
    def getInterfaceForContainedObjects(self):
        return IDisease
