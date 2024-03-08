# encoding: utf-8

'''🧬 EDRN Site: biomarker submission.'''

from django.conf import settings
from django.core.management.base import BaseCommand
from edrnsite.content.models import BiomarkerSubmissionFormPage
from eke.biomarkers.models import BiomarkerIndex
from wagtail.rich_text import RichText


_intro = RichText('<p>Fill out the following form in order to inform the Early Detection Research Network of a new biomarker being researched.</p>')
_outro = RichText('<p>Please double-check your email address as this will be the primary form of followup communication.')


class Command(BaseCommand):
    '''The EDRN "biomarker submission" command".'''

    help = 'Adds the biomarker submit form'

    def handle(self, *args, **options):
        '''Handle the EDRN `edrn_meta_descs` command.'''
        old = getattr(settings, 'WAGTAILREDIRECTS_AUTO_CREATE', True)
        try:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = False
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = False

            self.stdout.write('Nuking any existing BiomarkerSubmissionFormPages')
            BiomarkerSubmissionFormPage.objects.all().delete()

            parent = BiomarkerIndex.objects.first()
            if not parent:
                raise ValueError('No BiomarkerIndex page found')

            page = BiomarkerSubmissionFormPage(
                title='Biomarker Submission Form', intro=_intro, outro=_outro, slug='biomarker-submission-form',
                from_address='no-reply@nih.gov',
                to_address='sean.kelly@jpl.nasa.gov',
                subject='A new biomarker has been submitted'
            )
            parent.add_child(instance=page)
            page.save()
        finally:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = old
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
            self.stdout.write("Job's done!")
