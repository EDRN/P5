# encoding: utf-8

u'''Ingest RDF and create objects.'''

from .errors import IngestDisabled
from .interfaces import IIngestor
from .utils import IngestConsequences
from datetime import datetime
from five import grok
from plone.app.layout.navigation.interfaces import INavigationRoot
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
import logging, transaction, plone.api


_logger = logging.getLogger(__name__)
_dawnOfTime = datetime(1970, 1, 1, 0, 0, 0, 0)


class RDFIngestor(grok.View):
    u'''Ingest the RDF'''
    grok.context(INavigationRoot)
    grok.name('ingestRDF')
    grok.require('cmf.ManagePortal')
    def update(self):
        self.request.set('disable_border', True)
        registry = getUtility(IRegistry)
        ingestStart = registry['eke.knowledge.interfaces.IPanel.ingestStart']
        self.completeResults, self.skipped = IngestConsequences([], [], []), []
        if ingestStart and ingestStart > _dawnOfTime:
            self.ingestStart, self.ingestRunning = ingestStart, True
        else:
            try:
                registry['eke.knowledge.interfaces.IPanel.ingestStart'] = datetime.now()
                transaction.commit()
                paths = registry['eke.knowledge.interfaces.IPanel.objects']
                if not paths: return
                portal = plone.api.portal.get()
                for path in paths:
                    folder = portal.unrestrictedTraverse(path.encode('utf-8'))
                    ingestor = IIngestor(folder)
                    try:
                        results = ingestor.ingest()
                        transaction.commit()
                        self.completeResults.created.extend(results.created)
                        self.completeResults.updated.extend(results.updated)
                        self.completeResults.deleted.extend(results.deleted)
                    except IngestDisabled:
                        self.skipped.append(folder)
            finally:
                self.ingestRunning = False
                registry['eke.knowledge.interfaces.IPanel.ingestStart'] = _dawnOfTime
                self.completeResults.created.sort(lambda a, b: cmp(a.title, b.title))
                self.completeResults.updated.sort(lambda a, b: cmp(a.title, b.title))
                self.completeResults.deleted.sort()
                self.skipped.sort(lambda a, b: cmp(a.title, b.title))
                transaction.commit()
