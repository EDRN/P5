# encoding: utf-8

'''😌 EDRN Site Content: create explorer.'''

from django.conf import settings
from django.core.management.base import BaseCommand
from edrnsite.content.models import FlexPage, CDEExplorerPage
from edrnsite.policy.management.commands.utils import set_site
from wagtail.rich_text import RichText


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
        dest.body.append(('rich_text', RichText(f'<p><strong>New</strong>: explore the <a id="{page.pk}" linktype="page">{link_text}</a>.</p>')))
        dest.save()

    def _install_cde_explorer(self, home_page):
        self.stdout.write('Installing the official CDE Explorer')

        CDEExplorerPage.objects.all().delete()
        dest = FlexPage.objects.descendant_of(home_page).filter(slug='cde').first()
        assert dest is not None

        page = CDEExplorerPage(
            title='EDRN Data Model', live=True, show_in_menus=False,
            spreadsheet_id='1PAVUvmi0J-j6fK5dpltRIW8vRzVjh4kzpNReGFOQIe4',
            search_description='A tree-like explorer of the Common Data Elements (CDEs) of the Early Detection Research Network.',
        )
        dest.add_child(instance=page)
        page.save()
        page.update_nodes()
        self._append_link_to_page(dest, 'EDRN Data Model', page)

    def handle(self, *args, **options):
        self.stdout.write('Installing explorers')

        old = getattr(settings, 'WAGTAILREDIRECTS_AUTO_CREATE', True)
        try:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = False
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = False
            site, home_page = set_site()
            self._install_cde_explorer(home_page)

        finally:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = old
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
            self.stdout.write("Job's done!")
