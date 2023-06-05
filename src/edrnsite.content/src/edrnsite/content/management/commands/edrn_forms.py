# encoding: utf-8

'''😌 EDRN Site Content: create new forms.'''

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from edrnsite.policy.management.commands.utils import set_site
from wagtail.documents.models import Document
from wagtail.models import Page, PageViewRestriction
from wagtail.rich_text import RichText
from edrnsite.content.models import (
    MetadataCollectionFormPage, DatasetMetadataFormPage, FlexPage, PostmanAPIPage, SantiagoTaxonomyPage,
    TreeExplorerPage
)
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

    def _append_link_to_page(self, dest, link_text, page):
        '''Append a link to a ``page`` with the given ``link_text`` to the body stream on the ``dest`` page.

        There has GOT to be a better way of doing this!
        '''
        blocks = dest.body.get_prep_value()
        while True:
            try:
                dest.body.pop()
            except IndexError:
                break
        for block in blocks:
            if block['type'] == 'rich_text':
                dest.body.append(('rich_text', RichText(block['value'])))
            else:
                raise ValueError(f'Unexpected block type {block["type"]}')
        dest.body.append(('rich_text', RichText(f'<p><a id="{page.pk}" linktype="page">{link_text}</a></p>')))
        dest.save()

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
        self._append_link_to_page(dest, 'Dataset Metadata Form', page)
        dest.save()

    def _install_api(self, home_page):
        self.stdout.write('Installing LabCAS API page')
        PostmanAPIPage.objects.all().delete()
        dest = FlexPage.objects.descendant_of(home_page).filter(slug='labcas-metadata-and-common-data-elements').first()
        assert dest is not None
        postman = pkg_resources.resource_string(__name__, 'content/postman.json').decode('utf-8').strip()
        swagger = pkg_resources.resource_string(__name__, 'content/swagger.yaml').decode('utf-8').strip()
        postmanerator = pkg_resources.resource_string(__name__, 'content/postmanerator.html').decode('utf-8').strip()
        page = PostmanAPIPage(
            title='LabCAS API',
            postman=postman,
            swagger=swagger,
            postmanerator=postmanerator,
            live=True,
            show_in_menus=False
        )
        dest.add_child(instance=page)
        page.save()
        self._append_link_to_page(dest, 'LabCAS API', page)
        pvr = PageViewRestriction(restriction_type=PageViewRestriction.LOGIN, page=page)
        pvr.save()

    def _install_taxonomy(self, home_page):
        self.stdout.write('Installing LabCAS taxonomy diagram')
        SantiagoTaxonomyPage.objects.all().delete()
        dest = FlexPage.objects.descendant_of(home_page).filter(slug='labcas-metadata-and-common-data-elements').first()
        assert dest is not None
        with pkg_resources.resource_stream(__name__, 'content/labcas-tax.js') as io:
            file = File(io, name='labcas-tax.js')
            doc = Document(title='LabCAS Taxonomy JavaScript', file=file)
            doc.save()
        page = SantiagoTaxonomyPage(
            title='LabCAS CDE Taxonomy', taxonomy=doc, live=True, show_in_menus=False,
            search_description='A branching view of the LabCAS Common Data Elements.'
        )
        dest.add_child(instance=page)
        page.save()
        self._append_link_to_page(dest, 'LabCAS Taxonomy', page)

        self.stdout.write('Installing CDE explorer')
        TreeExplorerPage.objects.all().delete()
        dest.refresh_from_db()
        page = TreeExplorerPage(
            title='CDE Explorer', live=True, show_in_menus=False,
            search_description='A tree-like explorer of Common Data Elements (CDEs).'
        )
        dest.add_child(instance=page)
        page.save()
        self._append_link_to_page(dest, 'CDE Explorer', page)

    def handle(self, *args, **options):
        self.stdout.write('Moving existing metadata forms to the LabCAS CDE page')

        old = getattr(settings, 'WAGTAILREDIRECTS_AUTO_CREATE', True)
        try:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = False
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = False
            site, home_page = set_site()
            self._move_forms(home_page)
            self._install_forms(home_page)
            self._install_api(home_page)
            self._install_taxonomy(home_page)

        finally:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = old
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
            self.stdout.write("Job's done!")
