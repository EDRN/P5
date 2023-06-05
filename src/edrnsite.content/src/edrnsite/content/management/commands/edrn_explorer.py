# encoding: utf-8

'''😌 EDRN Site Content: create explorer.'''

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from edrnsite.policy.management.commands.utils import set_site
from wagtail.documents.models import Document
from wagtail.rich_text import RichText
from edrnsite.content.models import (
    SantiagoTaxonomyPage, TreeExplorerPage, FlexPage
)
import pkg_resources


class Command(BaseCommand):
    help = 'Install explorers'

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

    def _install_cde_explorers(self, home_page):
        self.stdout.write('Installing demo CDE explorers')

        TreeExplorerPage.objects.all().delete()
        dest = FlexPage.objects.descendant_of(home_page).filter(slug='labcas-metadata-and-common-data-elements').first()
        assert dest is not None

        page = TreeExplorerPage(
            title='CDE Explorer (attributes in panel)', live=True, show_in_menus=False, demo_mode='compact',
            search_description='A tree-like explorer of Common Data Elements (CDEs).'
        )
        dest.add_child(instance=page)
        page.save()
        self._append_link_to_page(dest, 'CDE Explorer (attributes separate)', page)

        page = TreeExplorerPage(
            title='CDE Explorer (attributes as nodes)', live=True, show_in_menus=False, demo_mode='full',
            search_description='A tree-like explorer of Common Data Elements (CDEs).'
        )
        dest.add_child(instance=page)
        page.save()
        self._append_link_to_page(dest, 'CDE Explorer (attributes as nodes)', page)

    def handle(self, *args, **options):
        self.stdout.write('Installing explorers')

        old = getattr(settings, 'WAGTAILREDIRECTS_AUTO_CREATE', True)
        try:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = False
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = False
            site, home_page = set_site()
            self._install_taxonomy(home_page)
            self._install_cde_explorers(home_page)

        finally:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = old
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
            self.stdout.write("Job's done!")
