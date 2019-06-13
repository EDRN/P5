# encoding: utf-8


u'''EKE Knowledge: Body System Folder'''

from .base import Ingestor
from .bodysystem import IBodySystem
from .knowledgefolder import IKnowledgeFolder
from five import grok


class IBodySystemFolder(IKnowledgeFolder):
    u'''Body system (organ) folder.'''


class BodySystemIngestor(Ingestor):
    grok.context(IBodySystemFolder)
    def getInterfaceForContainedObjects(self, predicates):
        return IBodySystem
