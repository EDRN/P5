# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: add months to publications.'''


from django.conf import settings
from django.core.management.base import BaseCommand
from eke.knowledge.models import Publication


class Command(BaseCommand):
    help = 'Add months to publications'

    def fix_publications(self):
        pmids = Publication.objects.filter(month='').values_list('pubMedID', flat=True)
        breakpoint()

    def handle(self, *args, **options):
        self.stdout.write('Adding months to publications')

        old = getattr(settings, 'WAGTAILREDIRECTS_AUTO_CREATE', True)
        try:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = False
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = False
            self.fix_publications()
        finally:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = old
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
            self.stdout.write("Job's done!")
