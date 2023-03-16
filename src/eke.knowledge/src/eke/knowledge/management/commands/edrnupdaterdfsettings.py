# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: RDF settings updates.'''

from django.conf import settings
from django.core.management.base import BaseCommand
from wagtail.models import PageViewRestriction
from edrnsite.content.models import FlexPage, SectionPage, HomePage
from eke.knowledge.models import SiteIndex, RDFSource
import logging


_member_groups_rdf = 'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/member-groups/@@rdf'
_member_groups_name = 'Cancer Data Expo Member Groups'


class Command(BaseCommand):
    help = 'Updates settings for RDF ingest'

    def handle(self, *args, **options):
        old = getattr(settings, 'WAGTAILREDIRECTS_AUTO_CREATE', True)
        try:
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = False

            verbosity = int(options['verbosity'])
            root_logger = logging.getLogger('')
            if verbosity >= 3:
                root_logger.setLevel(logging.DEBUG)

            self.stdout.write('🍽️ Updating RDF ingest settings')

            # For 6.1.0, we add the new member group RDF source to the SiteIndex
            site_index = SiteIndex.objects.first()
            PageViewRestriction.objects.filter(page=site_index).all().delete()
            found = False
            for rdf_source in site_index.rdf_sources.all():
                if rdf_source.url == _member_groups_rdf:
                    found = True
                    continue
            if not found:
                self.stdout.write(f'➕ Adding RDF source {_member_groups_rdf} to {site_index.url}')
                site_index.rdf_sources.add(RDFSource(name=_member_groups_name, url=_member_groups_rdf, active=True))
                site_index.save()

            self.stdout.write('⌦ Deleting the static sites page')
            FlexPage.objects.filter(slug='sites').delete()
            # And now change the slug and title of the RDF based one to just be plain sites
            self.stdout.write('🏷️ Renaming the RDF-based sites page to plain "Sites" and making it appear in menus')
            site_index.title, site_index.slug, site_index.show_in_menus = 'Sites', 'sites', True
            site_index.save()

            # We then edit pages that had the static sites page to use the SiteIndex instead
            self.stdout.write('✍️ Editing links on about and home page to point to RDF-based sites page')
            about = SectionPage.objects.filter(slug='about-edrn').first()
            assert about is not None
            about.body[1].value['cards'][7]['page'] = site_index
            about.save()
            home = HomePage.objects.first()
            assert home is not None
            home.body[1].value['cards'][3]['links'][7]['internal_page'] = site_index
            home.save()

        finally:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = old
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
            self.stdout.write("Job's done!")
