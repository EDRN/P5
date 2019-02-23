# encoding: utf-8


u'''EKE Knowledge: Publication Folder'''

from .base import Ingestor
from .publication import IPublication
from .knowledgefolder import IKnowledgeFolder
from five import grok


class IPublicationFolder(IKnowledgeFolder):
    u'''Publication folder.'''


class PublicationIngestor(Ingestor):
    grok.context(IPublicationFolder)
    def getInterfaceForContainedObjects(self):
        return IPublication
