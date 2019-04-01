# encoding: utf-8


u'''EKE Knowledge: Publication Folder'''

from . import _
from .base import Ingestor
from .publication import IPublication
from .knowledgefolder import IKnowledgeFolder
from Acquisition import aq_inner
from zope import schema
from five import grok
import contextlib, urllib2


class IPublicationFolder(IKnowledgeFolder):
    u'''Publication folder.'''
    pubSumDataSource = schema.TextLine(
        title=_(u'Summary Data Source'),
        description=_(u'URL to a source of summary statistics that describes publications in this folder.'),
        required=False,
    )
    dataSummary = schema.Text(
        title=_(u'Data Summary'),
        description=_(u'JSON data that describe summary information for the data in this folder.'),
        required=False,
    )


class PublicationIngestor(Ingestor):
    grok.context(IPublicationFolder)
    def getInterfaceForContainedObjects(self):
        return IPublication
    def getSummaryData(self, source):
        with contextlib.closing(urllib2.urlopen(source)) as bytestring:
            return bytestring.read()
    def ingest(self):
        context = aq_inner(self.context)
        consequences = super(PublicationIngestor, self).ingest()
        # Add summary data
        if context.pubSumDataSource:
            context.dataSummary = self.getSummaryData(context.pubSumDataSource)
        else:
            context.dataSummary = u'{}'
        return consequences


class PublicationSummary(grok.View):
    grok.context(IPublicationFolder)
    grok.require('zope2.View')
    grok.name('summary')
    def render(self):
        context = aq_inner(self.context)
        self.request.response.setHeader('Content-type', 'application/json; charset=utf-8')
        self.request.response.setHeader('Content-Transfer-Encoding', '8bit')
        return context.dataSummary
