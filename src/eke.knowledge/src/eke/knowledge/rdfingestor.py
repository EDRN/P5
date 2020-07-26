# encoding: utf-8

u'''Ingest RDF and create objects.'''

from .errors import IngestDisabled
from .interfaces import IIngestor
from .utils import IngestConsequences
from datetime import datetime
from Products.Five import BrowserView
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
import logging, transaction, plone.api


_logger = logging.getLogger(__name__)
DAWN_OF_TIME = datetime(1970, 1, 1, 0, 0, 0, 0)


class RDFIngestor(BrowserView):
    u'''Ingest the RDF'''
    def render(self):
        return self.index()
    def __call__(self):
        self.request.set('disable_border', True)
        registry = getUtility(IRegistry)
        ingestStart = registry['eke.knowledge.interfaces.IPanel.ingestStart']
        self.completeResults, self.skipped = IngestConsequences([], [], []), []
        if ingestStart and ingestStart > DAWN_OF_TIME:
            self.ingestStart, self.ingestRunning = ingestStart, True
        else:
            try:
                registry['eke.knowledge.interfaces.IPanel.ingestStart'] = datetime.now()
                transaction.commit()
                paths = registry['eke.knowledge.interfaces.IPanel.objects']
                if not paths: return
                portal = plone.api.portal.get()
                _logger.info('🏁 BEGIN FULL INGEST')
                for path in paths:
                    folder = portal.unrestrictedTraverse(path.encode('utf-8'))
                    try:
                        ingestor = IIngestor(folder)
                        results = ingestor.ingest()
                        transaction.commit()
                        self.completeResults.created.extend(results.created)
                        self.completeResults.updated.extend(results.updated)
                        self.completeResults.deleted.extend(results.deleted)
                    except TypeError:
                        _logger.exception(u"Can't adapt IIngestor to folder at path %s; skipping", path)
                        self.skipped.append(folder)
                    except IngestDisabled:
                        self.skipped.append(folder)
                    except Exception as ex:
                        # import pdb;pdb.set_trace()
                        _logger.exception(
                            u"SERIOUS? Got an exception %r on path %s; this could be bad, but skipping",
                            ex, path
                        )
                    # TODO except what else? We need a more graceful way to handle other exceptions
                    # like network outages
            finally:
                self.ingestRunning = False
                registry['eke.knowledge.interfaces.IPanel.ingestStart'] = DAWN_OF_TIME
                self.completeResults.created.sort(lambda a, b: cmp(a.title, b.title))
                self.completeResults.updated.sort(lambda a, b: cmp(a.title, b.title))
                self.completeResults.deleted.sort()
                self.skipped.sort(lambda a, b: cmp(a.title, b.title))
                transaction.commit()
                _logger.info('⏹ END FULL INGEST')
        return self.render()
