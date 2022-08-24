# encoding: utf-8

'''📦 EDRN Site Import from Plone: Plone Importer command.'''

from django.conf import settings
from django.core.management.base import BaseCommand
from edrnsite.ploneimport.classes import PloneExport
from edrnsite.policy.management.commands.utils import set_site
from wagtail.models import Page
import argparse


class Command(BaseCommand):
    help = 'Import into Wagtail from Plone export files'

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument('url', help='URL to PloneSite object')
        parser.add_argument('content-file', type=argparse.FileType('r'), help='Plone export ``edrn.json`` file')
        parser.add_argument('default-pages-file', type=argparse.FileType('r'), help='Plone default pages .json file')
        parser.add_argument('blobstorage-dir', help='Zope blobstorage directory')

    def get_container(self, home_page: Page):
        Page.objects.child_of(home_page).filter(title='Plone Export').delete()
        home_page.refresh_from_db()
        container = Page(title='Plone Export')
        home_page.add_child(instance=container)
        container.save()
        home_page.save()
        return container

    def handle(self, *args, **options):
        self.stdout.write('Importing Plone content')

        old = getattr(settings, 'WAGTAILREDIRECTS_AUTO_CREATE', True)
        try:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = False
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = False

            site, home_page = set_site()

            plone_export = PloneExport(
                options['url'], options['content-file'], options['default-pages-file'], options['blobstorage-dir']
            )
            export_container = self.get_container(home_page)
            plone_site = plone_export.get_import()
            plone_site.install(export_container)
            plone_site.rewrite_html()
        finally:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = old
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
