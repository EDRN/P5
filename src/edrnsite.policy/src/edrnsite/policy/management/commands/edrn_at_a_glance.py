# encoding: utf-8

'''🧬 EDRN Site: set up the "at-a-glance" page with a dashboard block.'''

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from edrnsite.content.models import FlexPage
from wagtail.models import Page


class Command(BaseCommand):
    '''Ensure the "at-a-glance" FlexPage has a dashboard block and no raw HTML.'''

    help = 'Create or update the "at-a-glance" page, removing any raw HTML block and adding a dashboard block.'

    def handle(self, *args, **options):
        '''Handle the EDRN `edrn_at_a_glance` command.'''
        try:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = False
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = False

            page = FlexPage.objects.filter(slug='at-a-glance').first()
            if page is None:
                parent = Page.objects.filter(slug='about-edrn').first()
                if parent is None:
                    raise CommandError('Cannot find the "about-edrn" page to use as a parent')
                self.stdout.write('No "at-a-glance" page found; creating it under "about-edrn"')
                page = FlexPage(
                    title='At a Glance', slug='at-a-glance', live=True,
                    meta_description='A summary of the Early Detection Research Network'
                    # search_image=wagtail.images.get_image_model().objects.filter(title='EDRN Logo').first()
                )
                parent.add_child(instance=page)
            else:
                self.stdout.write('Found existing "at-a-glance" page; emptying its body')
                page.body = []

            page.body.append(('dashboard', {}))  # You can override the settings in `{}` if you want
            self.stdout.write('🔍 Added the dashboard block to the "at-a-glance" page')
            page.save()
            self.stdout.write("Job's done!")
        finally:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = True
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
