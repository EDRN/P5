# encoding: utf-8

'''😌 EDRN Site Content: create explorer.'''

from django.conf import settings
from django.core.management.base import BaseCommand
from edrnsite.content.models import CDEExplorerPage
from edrnsite.policy.management.commands.utils import set_site


class Command(BaseCommand):
    help = 'Install explorers'

    def _update_cde_explorer(self, home_page):
        for page in CDEExplorerPage.objects.all():
            page.update_nodes()

    def handle(self, *args, **options):
        self.stdout.write('Updating CDE explorer')

        old = getattr(settings, 'WAGTAILREDIRECTS_AUTO_CREATE', True)
        try:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = False
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = False
            site, home_page = set_site()
            self._update_cde_explorer(home_page)

        finally:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = old
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
            self.stdout.write("Job's done!")
