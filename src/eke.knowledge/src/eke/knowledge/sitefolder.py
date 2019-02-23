# encoding: utf-8


u'''EKE Knowledge: Site Folder'''

from .base import Ingestor
from .knowledgefolder import IKnowledgeFolder
from .site import ISite
from five import grok
from plone.i18n.normalizer.interfaces import IIDNormalizer
from zope.component import getUtility
import urlparse


class ISiteFolder(IKnowledgeFolder):
    u'''Site folder.'''


class SiteIngestor(Ingestor):
    grok.context(ISiteFolder)
    def getInterfaceForContainedObjects(self):
        return ISite
    def getObjID(self, subjectURI, titles, predicates):
        if not titles: return None
        title = unicode(titles[0])
        if not title: return None
        normalize = getUtility(IIDNormalizer).normalize
        title = u'%s %s' % (urlparse.urlparse(subjectURI)[2].split('/')[-1], title)
        return normalize(title)
