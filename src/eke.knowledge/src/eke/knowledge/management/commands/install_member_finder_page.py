# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: publications associated with protocols.'''

from django.core.cache import caches
from django.core.management.base import BaseCommand
from eke.knowledge.models import MemberFinderPage
from wagtail.models import Site, Page


class Command(BaseCommand):
    '''Management command to install member finder as a Wagtail page model.'''

    help = 'Install member finder as a Wagtail page model'

    def handle(self, *args, **options):
        '''Handle the EDRN `install_member_finder_page` command.'''
        site = Site.objects.filter(is_default_site=True).first()
        assert site.site_name == 'Early Detection Research Network'

        self.stdout.write('Deleting any existing MemberFinderPages')
        MemberFinderPage.objects.descendant_of(site.root_page).delete()

        self.stdout.write("Finding the funding ops, which'll be the member finder's immediate left sibling")
        funding = Page.objects.filter(slug='funding-opportunities').first()
        assert funding is not None

        self.stdout.write('Creating the new MemberFinderPage')
        page = MemberFinderPage(
            title='Member Finder', live=True, show_in_menus=True,
            search_description='A tool to help you find members of the Early Detection Research Network'
        )
        funding.add_sibling(pos='right', instance=page)
        page.save()

        self.stdout.write('Clearing the caches')
        for cache in caches:
            caches[cache].clear()

        self.stdout.write("Job's done!")
