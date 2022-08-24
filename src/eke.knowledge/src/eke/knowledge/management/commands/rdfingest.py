# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: RDF ingest.'''

from django.core.management.base import BaseCommand
from eke.knowledge.site_ingest import full_ingest
from eke.knowledge.models import RDFIngest
from eke.knowledge.utils import aware_now
from wagtail.models import Site
import logging, humanize


class Command(BaseCommand):
    help = 'Ingests all portal data from its various RDF data sources'

    def handle(self, *args, **options):
        verbosity = int(options['verbosity'])
        root_logger = logging.getLogger('')
        if verbosity >= 3:
            root_logger.setLevel(logging.DEBUG)

        self.stdout.write('Starting RDF ingest')

        settings = RDFIngest.for_site(Site.objects.filter(is_default_site=True).first())
        t0 = aware_now()
        settings.last_ingest_start = t0

        newObjects, updatedObjects, deadURIs = full_ingest()

        delta = aware_now() - t0
        settings.last_ingest_duration = delta.total_seconds()
        settings.save()

        if verbosity >= 3:
            self.stdout.write(f'New objects created: {newObjects}')
            self.stdout.write(f'Objects updated: {updatedObjects}')
            self.stdout.write(f'Objects deleted: {deadURIs}')
            self.stdout.write(f'Total time: {humanize.precisedelta(delta)}')
        else:
            self.stdout.write(f'New objects created: {len(newObjects)}')
            self.stdout.write(f'Objects updated: {len(updatedObjects)}')
            self.stdout.write(f'Objects deleted: {len(deadURIs)}')
            self.stdout.write(f'Total time: {humanize.precisedelta(delta)}')
        self.stdout.write(self.style.SUCCESS('🎉 Ingest complete!'))
