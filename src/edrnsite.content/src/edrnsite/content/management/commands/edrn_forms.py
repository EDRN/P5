# encoding: utf-8

'''😌 EDRN Site Content: create new forms.'''

from django.conf import settings
from django.core.management.base import BaseCommand
from edrnsite.content.models import MetadataCollectionFormPage, DatasetMetadataFormPage, FlexPage
from edrnsite.policy.management.commands.utils import set_site
from wagtail.models import Page
from wagtail.rich_text import RichText
import pkg_resources


class Command(BaseCommand):
    help = 'Move existing forms and add new forms'

    def _move_forms(self, home_page):
        self.stdout.write('Moving MetadataCollectionFormPage to LabCAS CDE page')
        mcfp = MetadataCollectionFormPage.objects.descendant_of(home_page).first()
        assert mcfp is not None
        dest = Page.objects.descendant_of(home_page).filter(slug='labcas-metadata-and-common-data-elements').first()
        assert dest is not None
        if mcfp.get_parent() != dest:
            mcfp.move(dest, pos='last-child')

    def _install_forms(self, home_page):
        self.stdout.write('Installing new dataset metadata form')
        DatasetMetadataFormPage.objects.all().delete()
        dest = FlexPage.objects.descendant_of(home_page).filter(slug='labcas-metadata-and-common-data-elements').first()
        assert dest is not None
        intro = RichText(pkg_resources.resource_string(__name__, 'content/dataset-intro.html').decode('utf-8').strip())
        outro = RichText(pkg_resources.resource_string(__name__, 'content/dataset-outro.html').decode('utf-8').strip())
        page = DatasetMetadataFormPage(
            title='Dataset Metadata Form',
            intro=intro,
            outro=outro,
            from_address='ic-data@jpl.nasa.gov',
            to_address='sean.kelly@jpl.nasa.gov,heather.kincaid@jpl.nasa.gov',
            subject='New Dataset Metadata has been submitted'
        )
        dest.add_child(instance=page)
        page.save()

        # Append the link to the dataset form. There has GOT to be a better way of doing this!
        blocks = dest.body.get_prep_value()
        try:
            dest.body.pop()
        except IndexError:
            pass
        for block in blocks:
            if block['type'] == 'rich_text':
                dest.body.append(('rich_text', RichText(block['value'])))
            else:
                raise ValueError(f'Unexpected block type {block["type"]}')
        dest.body.append(('rich_text', RichText(f'<p><a id="{page.pk}" linktype="page">Dataset Metadata Form</a></p>')))
        dest.save()

    def handle(self, *args, **options):
        self.stdout.write('Moving existing metadata forms to the LabCAS CDE page')

        old = getattr(settings, 'WAGTAILREDIRECTS_AUTO_CREATE', True)
        try:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = False
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = False
            site, home_page = set_site()
            self._move_forms(home_page)
            self._install_forms(home_page)

        finally:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = old
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
            self.stdout.write("Job's done!")
