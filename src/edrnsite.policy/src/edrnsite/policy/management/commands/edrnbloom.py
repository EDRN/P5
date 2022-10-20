# encoding: utf-8

'''🧬 EDRN Site: initial population command.'''

from ._data import (
    GRANT_NUMBERS, BOILERPLATES, CERTIFICATIONS, SPONSOR_TOOL_URL, BLOG_URL, STUPID_TITLE, CAROUSEL_ALT_TEMPLATE,
    CAROUSEL_CAPTIONS, PREVENTION_SCIENCE_BLOG, MEETING_REPORTS_TEMPLATE, FIND_A_SPONSOR_TOOL_RICH_TEXT,
    INFORMATICS_BODY, MEMBER_FINDER_TEMPLATE, STATIC_SITES
)
from eke.knowledge.models import (
    PublicationIndex, BodySystemIndex, DiseaseIndex, MiscellaneousResourceIndex, SiteIndex, ProtocolIndex,
    DataCollectionIndex
)

from ._data import DATA_AND_RESOURCES as DAR
from ._data import SECTION_DESCRIPTIONS as SD
from .rdf import RDF_SOURCES
from .utils import set_site
from django.conf import settings
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from django.urls import reverse
from edrn.collabgroups.models import CollaborativeGroupSnippet
from edrnsite.content.models import HomePage, FlexPage, BoilerplateSnippet, CertificationSnippet, SectionPage
from edrnsite.controls.models import SocialMedia
from eke.biomarkers.models import BiomarkerIndex
from eke.geocoding.models import Geocoding
from eke.knowledge.publications import GrantNumber
from robots.models import Rule, DisallowedUrl
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.models import Site, Page
from wagtail.rich_text import RichText
from wagtail_favicon.models import FaviconSettings
from wagtailmenus.models import FlatMenu, FlatMenuItem
import pkg_resources, os


class Command(BaseCommand):
    help = 'Blooms an EDRN site with initial pages and data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--lite', action='store_true', default=False, help='Set up for lightweight ingest of just test data'
        )
        parser.add_argument(
            '--hostname', default='edrn.nci.nih.gov',
            help='Host name for the site (used for sitemaps etc.), defaults to %(default)s'
        )

    def _set_robots_txt(self, site: Site):
        DisallowedUrl.objects.all().delete()
        Rule.objects.all().delete()

        rule = Rule(robot='*')
        rule.save()
        rule.sites.add(site)
        url = DisallowedUrl(pattern='/')
        rule.disallowed.add(url)
        url.save()
        rule.save()

    def _set_settings(self, site: Site):
        '''Set up the settings, heh.'''

        # Social media
        sm = SocialMedia.objects.get_or_create(site_id=site.id)[0]
        sm.twitter = 'https://twitter.com/NCIPrevention'
        sm.facebook = 'https://www.facebook.com/cancer.gov'
        sm.save()

        # Favicon, manifest.json, and browser-config.xml support
        with pkg_resources.resource_stream(__name__, 'data/images/nih.png') as f:
            image_file = ImageFile(f, name='NIH')
            image = Image(title='National Institutes of Health', file=image_file)
            image.save()

            fi = FaviconSettings.objects.get_or_create(site_id=site.id)[0]
            fi.base_favicon_image = image
            fi.app_theme_color = '#319fbe'  # From the NCI Digital Style Guide, first primary palette color
            fi.app_name = 'Early Detection Research Network'
            fi.save()

        # Geocoding with AWS
        acc, sec = os.getenv('AWS_ACCESS_KEY_ID'), os.getenv('AWS_SECRET_ACCESS_KEY')
        if acc and sec:
            geo = Geocoding.objects.get_or_create(site_id=site.id)[0]
            geo.access_key, geo.secret_key = acc, sec
            geo.save()

    def _set_snippets(self):
        '''Set up initial textual snippets.'''

        # Set up the collaborative groups snippets
        for cg_code, name in (
            ('breast', 'Breast and Gynecologic Cancers Research Group'),
            ('gi', 'G.I. and Other Associated Cancers Research Group'),
            ('lung', 'Lung and Upper Aerodigestive Cancers Research Group'),
            ('prostate', 'Prostate and Urologic Cancers Research Group'),
        ):
            CollaborativeGroupSnippet.objects.get_or_create(cg_code=cg_code, name=name)

        # Add boilerplate
        for code, text in BOILERPLATES:
            BoilerplateSnippet.objects.get_or_create(bp_code=code, text=text)

        # Various lab certifications
        for url, label, description in CERTIFICATIONS:
            CertificationSnippet.objects.get_or_create(url=url, label=label, description=description)

    def _set_footer_menus(self, site: Site):
        FlatMenu.objects.all().delete()

        contact = FlatMenu(site=site, title='1: Contact', handle='footer-contact', heading='Contact DCP')
        contact.save()
        administrivia = Page.objects.filter(title='Administrivia').child_of(site.root_page).first()
        contact_info = Page.objects.filter(title='Contact Us').child_of(administrivia).first()
        FlatMenuItem(menu=contact, link_page=contact_info).save()

        info = FlatMenu(site=site, title='2: Information', handle='footer-info', heading='More Information')
        info.save()
        news_page = Page.objects.filter(title='News and Events').child_of(site.root_page).first()
        FlatMenuItem(menu=info, link_page=news_page, link_text='Get The Latest News').save()
        research_page = Page.objects.filter(title__startswith='Five').first()
        FlatMenuItem(menu=info, link_page=research_page, link_text='Learn About Our Research').save()

        policies = FlatMenu(site=site, title='3: Policies', handle='footer-policies', heading='Policies')
        policies.save()
        FlatMenuItem(
            menu=policies, link_url='https://www.cancer.gov/policies/accessibility', link_text='Accessibility'
        ).save()
        FlatMenuItem(
            menu=policies, link_url='https://www.cancer.gov/policies/disclaimer', link_text='Disclaimer'
        ).save()
        FlatMenuItem(menu=policies, link_url='https://www.cancer.gov/policies/foia', link_text='FOIA').save()
        FlatMenuItem(
            menu=policies, link_url='https://www.cancer.gov/policies/privacy-security', link_text='Privacy & Security'
        ).save()
        FlatMenuItem(
            menu=policies, link_url='https://www.hhs.gov/vulnerability-disclosure-policy/index.html',
            link_text='HHS Vulnerability Disclosure'
        ).save()

    def _write_homepage(
        self, homepage: HomePage, datapage: SectionPage, datapages: list, workpage: SectionPage, newspage: SectionPage,
        aboutpage: SectionPage
    ):
        '''Write the content of the ``homepage``.

        ``datapage`` is the page of the "Data and Resources" section, while ``datapages`` is a list of
        pages to include in the "Data and Resources" card.
        '''

        homepage.body = []

        # First up, a 3-image carousel
        images = []
        for name, label, caption in (
            ('cell', CAROUSEL_CAPTIONS[0][0], CAROUSEL_CAPTIONS[0][1]),
            ('bone-cancer', CAROUSEL_CAPTIONS[1][0], CAROUSEL_CAPTIONS[1][1]),
            ('biosensor', CAROUSEL_CAPTIONS[2][0], CAROUSEL_CAPTIONS[2][1])
        ):
            with pkg_resources.resource_stream(__name__, 'data/images/carousel-' + name + '.jpg') as f:
                image_file = ImageFile(f, name='carousel-' + name)
                image = Image(title=CAROUSEL_ALT_TEMPLATE.format(name), file=image_file)
                image.save()
                images.append({'image': image, 'caption': caption, 'label': label})
        homepage.body.append(('carousel', {'media': images}))

        # Next, the four major section cards. First we need their images
        images = {}
        for name in ('data', 'work', 'news', 'about'):
            with pkg_resources.resource_stream(__name__, 'data/images/home-' + name + '.jpg') as f:
                image_file = ImageFile(f, name='home-' + name)
                image = Image(title=f'Home page image for the ‘{name}’ section', file=image_file)
                image.save()
                images[name] = image

        # Now for "Work with EDRN" card, we need to insert a special external link and the member finder
        worklinks = [
            {'link_text': i.title, 'internal_page': i} for i in workpage.get_children() if i.show_in_menus
        ]
        sponsor_tool = {'link_text': 'Find a Sponsor Tool', 'external_link': SPONSOR_TOOL_URL}
        member_finder = {'link_text': 'Member Finder', 'view_name': 'find-members'}
        worklinks = worklinks[0:2] + [sponsor_tool] + [worklinks[2]] + [member_finder] + worklinks[3:]

        # And for the "News and Events" card, we need yet another special link
        newslinks = [
            {'link_text': i.title, 'internal_page': i} for i in newspage.get_children() if i.show_in_menus
        ]
        blog = {'link_text': 'Prevention Science blogs', 'external_link': BLOG_URL}
        newslinks = newslinks[0:3] + [blog] + newslinks[3:]

        # The about EDRN pages can be used with no extra manipulation
        aboutlinks = [
            {'link_text': i.title, 'internal_page': i} for i in aboutpage.get_children() if i.show_in_menus
        ]

        # And now we can put in the cards
        homepage.body.append(('section_cards', {'cards': [{
            'title': 'Data and Resources', 'style': 'aqua', 'image': images['data'], 'page': datapage,
            'links': [{'link_text': i.title, 'internal_page': i} for i in datapages]
        }, {
            'title': 'Work with EDRN', 'style': 'cerulean', 'image': images['work'], 'page': workpage,
            'links': worklinks
        }, {
            'title': 'News and Events', 'style': 'teal', 'image': images['news'], 'page': newspage,
            'links': newslinks,
        }, {
            'title': 'About EDRN', 'style': 'cyan', 'image': images['about'], 'page': aboutpage, 'links': aboutlinks
        }]}))
        homepage.save()

    def _write_workpage(self, workpage: SectionPage, heavy: bool):
        workpage.body.append(('title', {'text': 'Work with EDRN'}))

        # 1st: advocacy groups
        advocacy = Page.objects.filter(title='Advocacy Groups').first()
        assert advocacy is not None
        advocacy.move(workpage, pos='last-child')

        # 2nd: associate membership prog
        assoc = Page.objects.filter(title='Associate Membership Program').first()
        assert assoc is not None
        assoc.move(workpage, pos='last-child')

        # 3rd: find a sponsor tool; don't include in menus since the home page card has a direct link
        fast = FlexPage(title='Find a Sponsor Tool', live=True, show_in_menus=False)
        workpage.add_child(instance=fast)
        fast.body.append(('rich_text', FIND_A_SPONSOR_TOOL_RICH_TEXT))
        fast.save()

        mf = FlexPage(title='Member Finder', live=True, show_in_menus=False)
        workpage.add_child(instance=mf)
        member_finder_url = reverse('find-members')
        mf.body.append(('rich_text', RichText(MEMBER_FINDER_TEMPLATE.format(url=member_finder_url))))
        mf.save()

        # 4th: funding ops
        funds = Page.objects.filter(title='Funding Opportunities').first()
        assert funds is not None
        funds.move(workpage, pos='last-child')

        # 5th: validation study
        valid = Page.objects.filter(title='Propose a Validation Study').first()
        assert valid is not None
        valid.move(workpage, pos='last-child')

        # 6th: pub/priv partnerships
        partners = Page.objects.filter(title='Public-Private Partnerships').first()
        assert partners is not None
        partners.move(workpage, pos='last-child')

        # Next: memoranda of understanding
        mous = Page.objects.filter(title='Memoranda of Understanding').first()
        assert mous is not None
        mous.move(workpage, pos='last-child')

        workpage.body.append(('section_cards', {'cards': [
            {
                'title': 'Associate Membership Program', 'style': 'navy', 'description': SD['work']['assoc'],
                'page': assoc
            },
            {
                'title': 'Validation Study Proposals', 'style': 'navy', 'description': SD['work']['vsp'],
                'page': valid
            },
            {
                'title': 'Funding Opportunities', 'style': 'navy', 'description': SD['work']['funding'], 'page': funds
            },
            {
                'title': 'Advocacy Groups', 'style': 'navy', 'description': SD['work']['advocacy'], 'page': advocacy
            },
            {
                'title': 'Public-Private Partnerships', 'style': 'navy', 'description': SD['work']['pubpriv'],
                'page': partners
            },
            {
                'title': 'Find a Sponsor Tool', 'style': 'navy', 'description': SD['work']['tool'], 'page': fast
            },
            {
                'title': 'Memoranda of Understanding', 'style': 'navy', 'description': SD['work']['mous'],
                'page': mous
            },
            {
                'title': 'Member Finder', 'style': 'navy', 'description': SD['work']['mf'], 'page': mf
            }
        ]}))

    def _write_aboutpage(self, aboutEDRN: SectionPage, heavy: bool):
        aboutEDRN.body.append(('title', {'text': 'About the Early Detection Research Network'}))

        pages = {}
        for card_id, title in (
            ('mission', 'Mission and Structure'),
            ('fda', 'FDA-Approved Tests'),
            ('clia', 'CLIA-Approved Markers'),
            ('stupid', STUPID_TITLE),
            ('info', 'Informatics and Data Science'),
            ('history', 'History of the EDRN'),
            ('book', 'Bookshelf'),
        ):
            page = Page.objects.filter(title=title).first()
            assert page is not None, f'Page with title {title} not found'
            page.move(aboutEDRN, pos='last-child')
            pages[card_id] = page

        # DMCC won't have site data ready in time, so go ahead and create this, but not put it in menus
        sites = SiteIndex(
            title='Sites (RDF)', draft_title='Sites', seo_title='Sites', live=True, show_in_menus=False,
            ingest_order=50
        )
        sites.rdf_sources.add(*RDF_SOURCES['sites'][heavy])
        aboutEDRN.add_child(instance=sites)
        sites.save()

        # Then make a static version of the page
        sites = FlexPage(title='Sites', draft_title='Sites', seo_title='Sites', live=True, show_in_menus=True)
        sites.body.append(('rich_text', STATIC_SITES))
        aboutEDRN.add_child(instance=sites)
        sites.save()

        aboutEDRN.body.append(('section_cards', {'cards': [
            {
                'title': 'Mission and Structure', 'style': 'navy', 'description': SD['about']['mission'],
                'page': pages['mission']
            },
            {
                'title': 'FDA-Approved Tests', 'style': 'navy', 'description': SD['about']['fda'], 'page': pages['fda']
            },
            {
                'title': 'CLIA-Approved Markers', 'style': 'navy', 'description': SD['about']['clia'],
                'page': pages['clia']
            },
            {
                'title': STUPID_TITLE, 'style': 'navy', 'description': SD['about']['stupid'], 'page': pages['stupid']
            },
            {
                'title': 'Informatics and Data Science', 'style': 'navy', 'description': SD['about']['info'],
                'page': pages['info']
            },
            {
                'title': 'History of EDRN', 'style': 'navy', 'description': SD['about']['history'],
                'page': pages['history']
            },
            {
                'title': 'Bookshelf', 'style': 'navy', 'description': SD['about']['book'], 'page': pages['book']
            },
            {
                'title': 'Sites', 'style': 'navy', 'description': SD['about']['sites'], 'page': sites
            },
        ]}))
        aboutEDRN.save()

    def _create_administrivia(self, root):
        Page.objects.filter(title='Administrivia').child_of(root).delete()
        plone_administrivia = Page.objects.filter(title='Administrivia').first()
        contact_info = Page.objects.filter(title='Contact Us').child_of(plone_administrivia).first()
        administrivia = Page(title='Administrivia', show_in_menus=False, live=True)
        root.add_child(instance=administrivia)
        administrivia.save()
        contact_info.move(administrivia, pos='last-child')

    def _write_newspage(self, newspage: SectionPage):
        newspage.body.append(('title', {'text': 'News and Events'}))

        # 1st: newsletter
        newsletter = Page.objects.filter(title='EDRN Newsletter').first()
        assert newsletter is not None
        newsletter.move(newspage, pos='last-child')

        # 2nd: registration
        registration = Page.objects.filter(title='Upcoming Meetings').first()
        assert registration is not None
        registration.move(newspage, pos='last-child')

        # 3rd: reports
        reports = FlexPage(title='Meeting Reports', live=True, show_in_menus=True)
        newspage.add_child(instance=reports)
        meetings = {}
        for num in (38, 37, 36, 35):
            meeting = Page.objects.filter(title=f'{num}th Steering Committee Meeting').first()
            assert meeting is not None, f'Cannot find scmtg page for {num}'
            meetings[f'sc{num}'] = meeting.pk
        scimtg = Page.objects.filter(title='12th Scientific Workshop').first()
        assert scimtg is not None, 'Cannot find scientific meeting'
        meetings['scimtg'] = scimtg.pk
        reports.body.append(('rich_text', RichText(MEETING_REPORTS_TEMPLATE.format(**meetings))))
        reports.save()

        # 4th: blog; don't show in menus because the card for it on home page includes the direct link
        blog = FlexPage(title='Prevention Science Blog', live=True, show_in_menus=False)
        newspage.add_child(instance=blog)
        blog.body.append(('rich_text', PREVENTION_SCIENCE_BLOG))
        blog.save()

        # 5th and final: webinars
        webinars = Page.objects.filter(title='Webinars').first()
        assert webinars is not None
        webinars.move(newspage, pos='last-child')

        newspage.body.append(('section_cards', {'cards': [
            {
                'title': 'EDRN Newsletter', 'style': 'navy', 'description': SD['news']['newsletter'], 'page': newsletter
            },
            {
                'title': 'Meeting Reports', 'style': 'navy', 'description': SD['news']['reports'], 'page': reports
            },
            {
                'title': 'Prevention Science Blog', 'style': 'navy', 'description': SD['news']['blog'], 'page': blog
            },
            {
                'title': 'Webinars', 'style': 'navy', 'description': SD['news']['webinars'], 'page': webinars
            },
            {
                'title': 'Meeting Registration', 'style': 'navy', 'description': SD['news']['registration'],
                'page': registration
            },
        ]}))

    def _create_data_and_resources(self, homepage: HomePage, heavy: bool) -> tuple:
        pages_to_list, sub_pages = [], {}
        dar = SectionPage(
            title='Data and Resources', draft_title='Data and Resources', seo_title='Data and Resources',
            search_description='Scientific data, specimens, and other resources for the Early Detection Ressearch Network.',
            live=True, slug='data-and-resources', show_in_menus=True
        )
        homepage.add_child(instance=dar)
        dar.save()

        # The following appear in the menus and on the "data and resources" card:
        biomarkers = BiomarkerIndex(
            title='Biomarkers', draft_title='Biomarkers', seo_title='Biomarkers', live=True, show_in_menus=True,
            ingest_order=80,
        )
        biomarkers.rdf_sources.add(*RDF_SOURCES['biomarkers'][heavy])
        dar.add_child(instance=biomarkers)
        biomarkers.save()
        pages_to_list.append(biomarkers)
        sub_pages['biomarkers'] = biomarkers

        data = DataCollectionIndex(
            title='Data', draft_title='Data', seo_title='Data', live=True, show_in_menus=True,
            ingest_order=70
        )
        data.rdf_sources.add(*RDF_SOURCES['data'][heavy])
        dar.add_child(instance=data)
        data.save()
        pages_to_list.append(data)
        sub_pages['data'] = data

        p = FlexPage.objects.filter(title='Informatics').first()
        assert p is not None
        p.move(dar, pos='last-child')
        pages_to_list.append(p)
        sub_pages['informatics'] = p
        faq = FlexPage.objects.filter(title='Informatics FAQ').first()
        assert faq is not None
        faq.move(dar, pos='last-child')
        faq.show_in_menus = False

        protocols = ProtocolIndex(
            title='Protocols', draft_title='Protocols', seo_title='Protocols', live=True, show_in_menus=True,
            ingest_order=60
        )
        protocols.rdf_sources.add(*RDF_SOURCES['protocols'][heavy])
        dar.add_child(instance=protocols)
        protocols.save()
        pages_to_list.append(protocols)
        sub_pages['protocols'] = protocols

        publications = PublicationIndex(
            title='Publications', draft_title='Publications', seo_title='Publications', live=True, show_in_menus=True,
            ingest_order=40
        )
        publications.rdf_sources.add(*RDF_SOURCES['publications'][heavy])
        if heavy:
            publications.grant_numbers.add(*[GrantNumber(value=i) for i in GRANT_NUMBERS])
        else:
            publications.grant_numbers.add(GrantNumber(value='CA086368'))
        dar.add_child(instance=publications)
        publications.save()
        pages_to_list.append(publications)
        sub_pages['publications'] = publications

        # These also appear in menus and on the "data and resources" card:
        for identifier, title in (
            ('specimens', 'Specimen Reference Sets'),
            ('sop', 'Standard Operating Procedures'),
            ('stats', 'Statistical Resources')
        ):
            p = FlexPage.objects.filter(title=title).first()
            assert p is not None
            p.move(dar, pos='last-child')
            pages_to_list.append(p)
            sub_pages[identifier] = p

        # This one appears in menus, but not in the "data and resources" card on the home page
        p = FlexPage.objects.filter(title='EDRN Common Data Elements (CDEs)').first()
        assert p is not None
        p.move(dar, pos='last-child')
        sub_pages['cde'] = p

        # The next three don't appear in the menus or in the "data and resources" card:
        bodySystems = BodySystemIndex(
            title='Body Systems', draft_title='Body Systems', seo_title='Body Systems', live=True, show_in_menus=False,
            ingest_order=10
        )
        bodySystems.rdf_sources.add(*RDF_SOURCES['body-systems'][heavy])
        dar.add_child(instance=bodySystems)
        bodySystems.save()

        diseases = DiseaseIndex(
            title='Diseases', draft_title='Diseases', seo_title='Diseases', live=True, show_in_menus=False,
            ingest_order=20
        )
        diseases.rdf_sources.add(*RDF_SOURCES['diseases'][heavy])
        dar.add_child(instance=diseases)
        diseases.save()

        mrTitle = 'Miscellaneous Resources'
        miscResources = MiscellaneousResourceIndex(
            title=mrTitle, draft_title=mrTitle, seo_title=mrTitle, live=True, show_in_menus=False, ingest_order=30
        )
        miscResources.rdf_sources.add(*RDF_SOURCES['resources'][heavy])
        dar.add_child(instance=miscResources)
        miscResources.save()

        # Now set up the content on the data-and-resources page itself. First, the title.
        dar.body.append(('title', {'text': 'Data and Resources'}))

        # Gather the card dicts
        cards = []
        for identifier, title, description, alt_text in DAR:
            # Make the image for the card
            with pkg_resources.resource_stream(__name__, 'data/images/dr-' + identifier + '.jpg') as f:
                image_file = ImageFile(f, name='dr-' + identifier)
                image = Image(title=alt_text, file=image_file)
                image.save()
            cards.append({
                'title': title,
                'style': 'navy',
                'image': image,
                'page': sub_pages[identifier],
                'description': RichText(f'<p>{description}</p>'),
                'links': []
            })

        # And install 'em:
        dar.body.append(('section_cards', {'cards': cards}))
        dar.save()
        return dar, pages_to_list

    def _rewrite_informatics(self):
        page = FlexPage.objects.filter(title='Informatics').first()
        assert page.url == '/data-and-resources/informatics/'
        del page.body[0]
        faq = Page.objects.filter(title='Informatics FAQ').first()
        faq.show_in_menus = False
        faq.save()
        pks = {
            'informatics_faq': faq.pk,
            'biomarkers': Page.objects.filter(title='Biomarkers').first().pk,
            'protocols': Page.objects.filter(title='Protocols').first().pk,
            'publications': Page.objects.filter(title='Publications').first().pk,
            'data': Page.objects.filter(title='Data').first().pk,
            'cdes': Document.objects.filter(title='CDE Spreadsheet').first().pk
        }
        page.body.append(('rich_text', RichText(INFORMATICS_BODY.format(**pks))))
        page.save()

    def handle(self, *args, **options):
        self.stdout.write('Blooming "EDRN" site')

        try:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = False
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = False

            heavy = not options['lite']

            site, homePage = set_site(options['hostname'])
            self._set_settings(site)
            self._set_snippets()
            self._set_robots_txt(site)

            SectionPage.objects.all().delete()

            dataAndResources, dataAndResourcesPages = self._create_data_and_resources(homePage, heavy)

            workWithEDRN = SectionPage(
                title='Work with EDRN', draft_title='Work with EDRN', seo_title='Work with EDRN',
                search_description='Cooperative and collaborative opportunities, funding opportunities, studies, and more.',
                live=True, slug='work-with-edrn', show_in_menus=True
            )
            homePage.add_child(instance=workWithEDRN)
            self._write_workpage(workWithEDRN, heavy)
            workWithEDRN.save()

            newsAndEvents = SectionPage(
                title='News and Events', draft_title='News and Events', seo_title='News and Events',
                search_description='Announcements, noteworthy information, and occasions (both special and otherwise) for EDRN.',
                live=True, slug='news-and-events', show_in_menus=True
            )
            homePage.add_child(instance=newsAndEvents)
            self._write_newspage(newsAndEvents)
            newsAndEvents.save()

            self._create_administrivia(homePage)

            aboutEDRN = SectionPage(
                title='About EDRN', draft_title='About EDRN', seo_title='About EDRN', slug='about-edrn', live=True,
                search_description='All about the Early Detection Research Network.', show_in_menus=True,
            )
            homePage.add_child(instance=aboutEDRN)
            self._write_aboutpage(aboutEDRN, heavy)
            self._write_homepage(homePage, dataAndResources, dataAndResourcesPages, workWithEDRN, newsAndEvents, aboutEDRN)

            self._set_footer_menus(site)

            # And lastly, drop anything we didn't import from Plone
            Page.objects.filter(title='Plone Export').child_of(homePage).delete()

            # Rewrite the Informatics page
            self._rewrite_informatics()
        finally:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = True
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
