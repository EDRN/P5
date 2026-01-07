# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: add the forbidden publications.'''


from typing import Any


from django.core.management.base import BaseCommand, CommandError
from eke.knowledge.models import PublicationIndex, ForbiddenPublication, Publication, PMCID

_forbidden_pubmed_IDs = set(['4083999'])


class Command(BaseCommand):
    help = 'Add the forbidden publications to the site'

    def add_forbidden_publications(self):
        if PublicationIndex.objects.count() == 0:
            self.stderr.write('🐇 No publication index found, so skipping forbidden publications')
            return
        elif PublicationIndex.objects.count() > 1:
            raise CommandError('😵‍💫 Multiple publication indexes found which should not happen!')
        publication_index = PublicationIndex.objects.first()

        for pmid in _forbidden_pubmed_IDs:
            fp, created = ForbiddenPublication.objects.get_or_create(value=pmid, page=publication_index)
            if created:
                self.stdout.write(f'➕ Added forbidden publication {pmid}')
            else:
                self.stdout.write(f'🔍 Forbidden publication {pmid} already exists')

            pmcids = PMCID.objects.filter(pmid=pmid)
            self.stdout.write(f'⌫ Removing {pmcids.count()} PMCIDs for {pmid}')
            pmcids.delete()

            pubs = Publication.objects.filter(pubMedID=pmid)
            self.stdout.write(f'⌫ Removing {pubs.count()} publications for {pmid}')
            pubs.delete()

    def handle(self, *args, **options):
        self.stdout.write('🔍 Adding the forbidden publications to the site')

        self.add_forbidden_publications()
        self.stdout.write("🎉 Job's done!")
