# encoding: utf-8


u'''EKE Knowledge: Site Folder'''

from .base import Ingestor
from .knowledgefolder import IKnowledgeFolder, KnowledgeFolderView
from .protocol import IProtocol
from Acquisition import aq_inner
from five import grok
from plone.memoize.view import memoize
from zope.component import getUtility
import urlparse, logging, plone.api


_logger = logging.getLogger(__name__)


class IProtocolFolder(IKnowledgeFolder):
    u'''Protocol folder.'''


class ProtocolIngestor(Ingestor):
    grok.context(IProtocolFolder)
    def getInterfaceForContainedObjects(self):
        return IProtocol
