# encoding: utf-8

'''📦 EDRN Site Import from Plone: Plone Importer command.'''

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db.models.functions import Lower
from edrn.collabgroups.models import Committee
from edrnsite.content.models import FlexPage
from edrnsite.ploneimport.classes import PaperlessExport, PlonePage
from edrnsite.policy.management.commands.utils import set_site
from eke.knowledge.models import CommitteeIndex, RDFSource, SiteIndex
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.models import Page, PageViewRestriction
from wagtail.rich_text import RichText
import argparse, pkg_resources


_committees_url = 'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/committees/@@rdf'

NCT_GROUP_ACCESS = [
    'Feng Fred Hutchinson Cancer Center',
    'Feng Fred Hutchinson Cancer Research Center',
    'Portal Content Custodian',
    'Srivastava National Cancer Institute',
    'Steering Committee',
    'Super User'
]

# triples here are the group ID in dMCC soap, LDAP group, and description
_groups = {
    # These appear in RDF but have no members, no docs, no events, and no apparent purpose:
    # 'associate-member': (33, None, 'No description available.'),
    # 'biomarker-developmental-laboratories': (27, None, 'No description available.'),
    # 'biomarker-reference-laboratories': (28, None, 'No description available.'),
    # 'clinical-epidemiology-and-validation-center': (29, None, 'No description available.'),
    # 'jet-propulsion-laboratory': (32, None, 'No description available.'),
    # 'national-cancer-institute': (31, None, 'No description available.'),

    'breast-and-gynecologic-cancers-research-group': (14, 'Breast and Gynecologic', 'No description available.'),
    'collaboration-and-publication-subcommittee': (7, None, '''The objective of the Collaboration and Publication Subcommittee is to define procedures and conditions for formal collaboration within the EDRN and with investigators outside the Network, and defines publication policies.'''),
    'communication-and-workshop-subcommittee': (6, None, '''The objective of the Communication and Workshop Subcommittee is to achieve the full potential of biomarkers as tools to facilitate early detection of cancer by disseminating research goals and findings with the broader components of the research enterprise. To accomplish this objective, the Communication and Workshop Subcommittee defines formats for exchange of scientific findings such as workshops, seminars, and electronic information resources that serve to inform the research communities of scientific advances.'''),
    'data-management-and-coordinating-center': (30, None, 'No description available.'),
    'data-sharing-and-informatics-subcommittee': (8, None, '''The objectives of the Data Sharing and Informatics Subcommittee are to establish guidelines for the EDRN data structure and common data items, and to provide a forum for biostatisticians/analysts within EDRN to collaborate on research pertinent to EDRN.'''),
    'erne-working-group': (10, None, 'No description available.'),
    'executive-committee': (2, 'Executive Committee', '''The Executive Committee (EC) consists of a Chair, Chair of the SC, Chairs of Collaborative Groups, at least one Principal Investigator from a BDL, BRL, CEVC, and DMCC (if not represented in the Collaborative Group Chairs), and the NCI Program Coordinator or a designee. The Committee is chaired by the Co-chair of the Steering Committee. The Committee expedites the work of the Steering Committee and assists the Chair of the Steering Committee. It coordinates the administrative and research activities of the EDRN on a regular basis and provides a mechanism for communication on the management of the EDRN. The Committee makes recommendations on major policy issues to the Steering Committee.'''),
    'g-i-and-other-associated-cancers-research-group': (15, 'G.I. and Other Associated', 'No description available.'),
    'lung-and-upper-aerodigestive-cancers-research-group': (16, 'Lung and Upper Aerodigestive', 'No description available.'),
    'network-consulting-team': (3, None, '''The Network Consulting Team (NCT) is composed of a Chair and non-EDRN members appointed by NCI. The NCT reviews the progress of the EDRN, recommends new research initiatives, and ensures that the Network is responsive to promising opportunities in early detection research and risk assessment. The number and composition of members is not fixed. The NCT has access to all EDRN research information including Progress Reports provided by individual investigators. The NCT can recommend new research projects to the Steering Committee or to NCI. Members of the Network Consulting Team can serve on ad-hoc Committees of the EDRN, Review Groups, and as consultants to Subcommittees. Members of the Network Consulting Team cannot apply for Associate Membership. Associate Members cannot serve on the Network Consulting Team. The NCT meets at least once a year.'''),
    'prioritization-subcommittee': (4, None, '''The objective of the Prioritization Subcommittee is to establish procedures for prioritizing research and allocating resources within the Network.'''),
    'prostate-and-urologic-cancers-research-group': (17, 'Prostate and Urologic', 'No description available.'),
    'technology-and-resource-sharing-subcommittee': (5, None, '''The objective of the Technology and Resource Sharing Subcommittee is to establish the rationale and conditions for sharing technology and other resources among investigators within and external to the EDRN.'''),
}


class Command(BaseCommand):
    help = 'Import the "paperless" files'

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument('content-file', type=argparse.FileType('r'), help='Plone export ``edrn.json`` file')
        parser.add_argument('blobstorage-dir', help='Zope blobstorage directory')

    def write_index(self, page: FlexPage, custom_label='<p>This group contains the following itesm:</p>'):
        if page.get_children().count() == 0:
            page.body.append(('rich_text', RichText('<p>There are no items in this group.</p>')))
        else:
            page.body.append(('rich_text', RichText(custom_label)))
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

    def create_groups_container(self, parent: Page) -> Page:
        index = parent.get_children().filter(slug='groups').first()
        if index is not None:
            index.delete()
            parent.refresh_from_db()
        index = CommitteeIndex(
            title='Committees and Collaborative Groups', slug='groups', live=True, show_in_menus=False,
            ingest_order=90, seo_title='Committees', draft_title='Groups'
        )
        index.rdf_sources.add(RDFSource(name='DMCC Committees', url=_committees_url, active=True))
        parent.add_child(instance=index)
        index.save()
        return index

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
        nct_group = Page.objects.filter(title='Committees and Collaborative Groups').first().get_descendants().filter(title='Network Consulting Team').first()
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

    def create_groups(self, site, home_page: Page, mission_and_structure: Page, source: PlonePage):
        '''Create the new groups container.'''
        plone_committees = {i.item_id: i for i in source.children}

        groups = mission_and_structure.get_children().filter(slug='groups').first()
        assert groups is not None
        groups.get_children().exclude(slug='steering-committee').delete()
        current_steering_committee = groups.get_children().filter(slug='steering-committee').first()
        assert current_steering_committee is not None
        current_steering_committee.move(home_page, pos='last-child')
        current_steering_committee.refresh_from_db()
        groups.refresh_from_db()
        home_page.refresh_from_db()
        mission_and_structure.get_children().filter(slug='groups').delete()
        mission_and_structure.refresh_from_db()
        groups = self.create_groups_container(mission_and_structure)
        for key, attributes in _groups.items():
            id_number, ldap_group, description = attributes
            committee = Committee(
                title=plone_committees[key].title, slug=key, live=True, id_number=id_number,
                description=description
            )
            groups.add_child(instance=committee)
            committee.save()
            for doc in [i for i in plone_committees[key].children if i is not None]:
                doc.install(committee)
                doc.rewrite_html()

            if key == 'network-consulting-team':
                pvr = PageViewRestriction(page=committee, restriction_type='groups')
                pvr.save()
                pvr.groups.set(Group.objects.filter(name__in=NCT_GROUP_ACCESS), clear=True)
            elif ldap_group:
                pvr = PageViewRestriction(page=committee, restriction_type='groups')
                pvr.save()
                pvr.groups.set(Group.objects.filter(name=ldap_group), clear=True)

        new_steering_committee = Committee(
            title='Steering Committee', slug='steering-committee', live=True, id_number='1',
            description='''The Steering Committee (SC) has major scientific management oversight and responsibility for developing and implementing a collaborative Network research program including protocols, publications, and design. The Committee consists of a Chair, Co-chair, the EDRN Principal Investigators or a designee, and the NCI Program Coordinator or a designee. Members of the SC review all data collected in Network studies, monitor study results, follow-up, and report to the full SC upon request of the Chair. Each member has one vote.'''
        )
        groups.add_child(instance=new_steering_committee)
        pvr = PageViewRestriction(page=new_steering_committee, restriction_type='groups')
        pvr.save()
        pvr.groups.set(Group.objects.filter(name='Steering Committee'), clear=True)
        new_steering_committee.save()
        for page in current_steering_committee.get_children():
            page.move(new_steering_committee, pos='last-child')
        site.root_page.get_children().filter(slug='steering-committee').delete()

    def move_rdf_sites(self, site, home_page):
        FlexPage.objects.filter(slug='sites').delete()
        sites = SiteIndex.objects.filter(slug='sites-rdf').first()
        assert sites is not None
        sites.title, sites.slug = 'Sites', 'sites'
        sites.save()

    def rewrite_mission_and_structure(self, site, home_page):
        mas = FlexPage.objects.filter(slug='mission-and-structure').first()
        assert mas is not None
        del mas.body[0]
        body = pkg_resources.resource_string(__name__, 'data/mas.html').decode('utf-8').strip()
        pks = {
            'org_chart': Image.objects.filter(title='New Organization Chart').first().pk,
            'sites': SiteIndex.objects.first().pk,
        }
        mas.body.append(('rich_text', RichText(body.format(**pks))))
        mas.save()

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
            self.create_groups(site, home_page, mission_and_structure, plone_groups)
            self.create_network_consulting_team(home_page, nct)
            self.move_rdf_sites(site, home_page)
            self.rewrite_mission_and_structure(site, home_page)

        finally:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = old
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
