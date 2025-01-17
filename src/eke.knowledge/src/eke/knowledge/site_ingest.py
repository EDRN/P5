# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: site ingest.'''

from .models import RDFIngest, KnowledgeFolder
from .utils import get_class
from django.conf import settings
from django.core.management import call_command
from wagtail.models import Site
import logging


_logger = logging.getLogger(__name__)


def full_ingest():
    '''Do a full ingest of every RDF-enabled knowledge folder on the site.'''

    try:
        # Assumption: the default site is the EDRN site
        site = Site.objects.filter(is_default_site=True).first()
        rdfSettings = RDFIngest.for_site(site)
        if not rdfSettings.enabled:
            raise ValueError('RDF ingest is disabled for site %r', site)

        newObjects, updatedObjects, deadURIs = set(), set(), set()
        folders = KnowledgeFolder.objects.all().filter(ingest=True).order_by('ingest_order').specific()
        settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = False
        _logger.info('Commencing ingest for the following: %s', ', '.join([i.url for i in folders]))
        for folder in folders:
            try:
                if isinstance(folder.RDFMeta.ingestor, str):
                    cls = get_class(folder.RDFMeta.ingestor)
                else:
                    cls = folder.RDFMeta.ingestor
                ingestor = cls(folder)
                n, u, d = ingestor.ingest()
                newObjects |= n
                updatedObjects |= u
                deadURIs |= d
            except Exception as ex:
                _logger.exception(f'⚠️ Error "{ex}" encounted at folder {folder.url}; continuing on')

        _logger.info(
            '🥳 Ingest completed with %d new objects, %d updated objects, and %d deleted',
            len(newObjects), len(updatedObjects), len(deadURIs)
        )
        return newObjects, updatedObjects, deadURIs
    finally:
        settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
        call_command('fixtree')
        call_command('wagtail_update_index')
