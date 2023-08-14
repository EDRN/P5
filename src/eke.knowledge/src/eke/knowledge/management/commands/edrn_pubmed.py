# encoding: utf-8

'''😌 EDRN Site Content: create explorer.'''

from django.conf import settings
from django.core.management.base import BaseCommand
from eke.knowledge.models import Publication, PublicationSubjectURI
import collections


class Command(BaseCommand):
    help = 'Replace duplicate publications with single ones based on PubMed ID'

    def fix_publications(self):
        c = 0
        to_do = Publication.objects.exclude(identifier__startswith='urn:miriam:pubmed:').values_list('pubMedID', flat=True)
        counter = collections.Counter([i for i in to_do])
        self.stdout.write(f'Found {len(counter)} unique PubMed IDs that need to be processed')
        for pmid, count in counter.most_common():
            if count > 1:
                # Just delete all the dupes for now; we can get them back on the next ingest
                self.stdout.write(f'Deleting {count-1} instance(s) of {pmid}')
                instances = Publication.objects.filter(pubMedID=pmid).all()
                publication = instances[0]
                for instance in instances[1:]:
                    instance.delete()
                    del instance
                del instances
            elif count == 1:
                # For these, clear their ways so they can get reconnected to Sites and get new
                # PublicationSubjectURIs on the next ingest
                publication = Publication.objects.filter(pubMedID=pmid).first()
                assert publication is not None

            c += 1
            if c % 100 == 0:
                self.stdout.write(f'Fixing {pmid} to have no sites and a new RDF subject URI ({c} so far)')
            publication.site_that_wrote_this.clear()
            publication.siteID = ''
            publication.identifier = f'urn:miriam:pubmed:{pmid}'
            publication.save()
            del publication

        # None of these should exist yet, but I'm paranoid
        self.stdout.write('Deleting all PublicationSubjectURIs')
        PublicationSubjectURI.objects.all().delete()

    def handle(self, *args, **options):
        self.stdout.write('Deleting all publications')

        old = getattr(settings, 'WAGTAILREDIRECTS_AUTO_CREATE', True)
        try:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = False
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = False
            self.fix_publications()
        finally:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = old
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
            self.stdout.write("Job's done!")
