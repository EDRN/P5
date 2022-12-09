# encoding: utf-8

'''📦 EDRN Site Import from Plone: Plone Importer command.'''

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db.models.functions import Lower
from edrnsite.content.models import FlexPage
from edrnsite.ploneimport.classes import PaperlessExport, PlonePage
from edrnsite.policy.management.commands.utils import set_site
from wagtail.documents.models import Document
from wagtail.models import Page, PageViewRestriction
from wagtail.rich_text import RichText
import argparse, pkg_resources


NCT_GROUP_ACCESS = [
    'Feng Fred Hutchinson Cancer Center',
    'Feng Fred Hutchinson Cancer Research Center',
    'Portal Content Custodian',
    'Srivastava National Cancer Institute',
    'Steering Committee',
    'Super User'
]


class Command(BaseCommand):
    help = 'Import the "paperless" files'

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument('content-file', type=argparse.FileType('r'), help='Plone export ``edrn.json`` file')
        parser.add_argument('blobstorage-dir', help='Zope blobstorage directory')

    def write_index(self, page: FlexPage):
        if page.get_children().count() == 0:
            page.body.append(('rich_text', RichText('<p>There are no items in this group.</p>')))
        else:
            page.body.append(('rich_text', RichText('<p>This group contains the following items:</p>')))
            text = '<ul class="list-unstyled">'
            for child in page.get_children().order_by(Lower('title')):
                text += f'<li><a id="{child.pk}" linktype="page">{child.title}</a></li>'
            text += '</ul>'
            page.body.append(('rich_text', RichText(text)))
        page.save()

    def get_plone_groups(self, about: PlonePage) -> PlonePage:
        for i in about.children:
            if i is not None:
                if i.item_id == 'mission-and-structure':
                    for j in i.children:
                        if j is not None:
                            if j.item_id == 'groups':
                                return j
        return None

    def create_folder(self, parent: Page, title: str) -> Page:
        '''Create a "folder" with the given ``title`` as a child of ``parent``, deleting it if it already
        exists. Return the newly created folder.
        '''
        folder = parent.get_children().filter(title=title).first()
        if folder is not None:
            folder.delete()
            parent.refresh_from_db()
        folder = FlexPage(title=title, live=True)
        parent.add_child(instance=folder)
        folder.save()
        return folder

    def create_groups_container(self, home_page: Page) -> Page:
        about = home_page.get_children().filter(slug='about-edrn').first()
        assert about is not None
        return self.create_folder(about, 'Groups')

    def create_network_consulting_team(self, home_page: Page, source: PlonePage):
        home_page.get_children().filter(title='Network Consulting Team').delete()
        home_page.refresh_from_db()
        nct_page = source.install(home_page)
        source.rewrite_html()

        overview = nct_page.get_children().filter(title='Overview').first().specific
        del overview.body[0]
        overview.body.append(('rich_text',
            RichText(pkg_resources.resource_string(__name__, 'data/overview.html').decode('utf-8').strip())
        ))
        overview.save()

        objectives = nct_page.get_children().filter(title='Objectives and Responsibilities').first().specific
        del objectives.body[0]
        objectives.body.append(('rich_text',
            RichText(pkg_resources.resource_string(__name__, 'data/objectives.html').decode('utf-8').strip())
        ))
        objectives.save()

        weird_page = Page.objects.filter(title='NCT 2020: New Docs NCT 2020 AVAILABLE').first()
        nct_group = Page.objects.filter(title='Groups').first().get_descendants().filter(title='Network Consulting Team').first()
        pks = {
            'nct_2020_new_docs_nct_2020_available': weird_page.pk,
            'network_consulting_team': nct_group.pk,
            'accomplishments': Document.objects.filter(title='EDRN Accomplishments November 2013').first().pk,
            'amp': Document.objects.filter(title='EDRN Associate Membership Program').first().pk,
            'pm': Document.objects.filter(title='EDRN Performance Metrics').first().pk,
            'h': Document.objects.filter(title='EDRN Scientific Research Highlights November 2013 (Updated)').first().pk,
            'sp': Document.objects.filter(title='EDRN Strategic Plan 2013 (Update 1)').first().pk,
            'overview': overview.pk,
            'objectives': objectives.pk,
            'past': nct_page.get_children().filter(slug='meetings').first().pk,
            'reports': nct_page.get_children().filter(slug='program-reports').first().pk
        }
        body = pkg_resources.resource_string(__name__, 'data/nct.html').decode('utf-8').strip()
        del nct_page.body[0]
        nct_page.body.append(('rich_text', RichText(body.format(**pks))))
        nct_page.show_in_menus = False
        nct_page.save()

        PageViewRestriction.objects.filter(page=nct_page).delete()
        pvr = PageViewRestriction(page=nct_page, restriction_type='groups')
        pvr.save()
        pvr.groups.set(Group.objects.filter(name__in=NCT_GROUP_ACCESS), clear=True)

        return nct_page

    def create_groups(self, home_page: Page, mission_and_structure: Page, source: PlonePage):
        groups = mission_and_structure.get_children().filter(slug='groups').first()
        assert groups is not None
        groups.get_children().exclude(slug='steering-committee').delete()
        groups.refresh_from_db()
        for child in [i for i in source.children if i is not None]:
            page = child.install(groups)
            child.rewrite_html()
            self.write_index(page)
            if page.slug == 'network-consulting-team':
                pvr = PageViewRestriction(page=page, restriction_type='groups')
                pvr.save()
                pvr.groups.set(Group.objects.filter(name__in=NCT_GROUP_ACCESS), clear=True)

    def handle(self, *args, **options):
        self.stdout.write('Importing Plone "paperless" content')

        old = getattr(settings, 'WAGTAILREDIRECTS_AUTO_CREATE', True)
        try:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = False
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = False

            site, home_page = set_site()

            # The `edrn.json` file has URL prefix as `http://nohost/edrn/` and therefore we no longer need to
            # get it as a command-line option.
            paperless = PaperlessExport('http://nohost/edrn/', options['content-file'], options['blobstorage-dir'])
            nct, plone_about = paperless.get_import().children
            plone_groups = self.get_plone_groups(plone_about)
            assert plone_groups is not None

            mission_and_structure = FlexPage.objects.filter(slug='mission-and-structure').first()
            assert mission_and_structure is not None
            self.create_groups(home_page, mission_and_structure, plone_groups)
            self.create_network_consulting_team(home_page, nct)

        finally:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = old
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
