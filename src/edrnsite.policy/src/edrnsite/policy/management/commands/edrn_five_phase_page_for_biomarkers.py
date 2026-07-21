# encoding: utf-8

'''🧬 EDRN Site: set up the five-phase page for the Biomarkers index.'''

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from edrnsite.content.models import FlexPage
from eke.biomarkers.models import BiomarkerIndex
from wagtail.models import Page


class Command(BaseCommand):
    '''Link the five-phase page for the Biomarkers index to the Biomarkers index page.'''

    help = 'Link the five-phase page for the Biomarkers index to the Biomarkers index page.'
    _horrible_slug = 'five-phase-approach-and-prospective-specimen-collection-retrospective-blinded-evaluation-study-design'

    def handle(self, *args, **options):
        '''Handle the EDRN `edrn_five_phase_page_for_biomarkers` command.'''
        try:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = False
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = False

            five_phase_page = FlexPage.objects.filter(slug=self._horrible_slug).first()
            biomarker_index = BiomarkerIndex.objects.first()

            if five_phase_page is None:
                self.stderr.write(f'Cannot find the five-phase page with slug {self._horrible_slug}; not linking')
                return
            if biomarker_index is None:
                self.stderr.write('Cannot find the Biomarkers index page; not linking')
                return

            self.stdout.write(f'Linking the five-phase page with slug {self._horrible_slug} to the Biomarkers index page')
            biomarker_index.five_phase_page = five_phase_page
            biomarker_index.save()
            self.stdout.write("Job's done!")

        finally:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = True
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
