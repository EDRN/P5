# encoding: utf-8

'''😌 EDRN Site Content: create new forms.'''

from django.conf import settings
from django.core.management.base import BaseCommand
from edrnsite.content.models import SpecimenReferenceSetRequestFormPage, MetadataCollectionFormPage, BoilerplateSnippet
from edrnsite.policy.management.commands.utils import set_site
from wagtail.models import Page
from wagtail.rich_text import RichText
from django.db.utils import IntegrityError
import pkg_resources


class Command(BaseCommand):
    help = 'Populate the site with the new forms'

    def _create_specimen_ref_set_req_form_page(self, home_page: Page):
        parent = home_page.get_descendants().filter(slug='specimen-reference-sets').first()
        assert parent is not None
        intro = RichText(pkg_resources.resource_string(__name__, 'content/spec-intro.html').decode('utf-8').strip())
        advice = RichText(pkg_resources.resource_string(__name__, 'content/spec-advice.html').decode('utf-8').strip())
        outro = RichText(pkg_resources.resource_string(__name__, 'content/spec-outro.html').decode('utf-8').strip())
        self.stdout.write('🧫 Creating the specimen reference set request form page')
        form_page = SpecimenReferenceSetRequestFormPage(
            title='Specimen Set Request Form',
            intro=intro,
            outro=outro,
            proposal_advice=advice,
            from_address='ic-portal@jpl.nasa.gov',
            to_address='sean.kelly@jpl.nasa.gov,heather.kincaid@jpl.nasa.gov',
            subject='A new Specimen Reference Set Request has been submitted'
        )
        parent.add_child(instance=form_page)
        form_page.save()

        self.stdout.write('👩‍⚖️ Adding boilerplate text for specimen requests')
        next_steps = pkg_resources.resource_string(__name__, 'content/spec-next-steps.html').decode('utf-8').strip()
        try:
            BoilerplateSnippet.objects.get_or_create(bp_code='specimen-request-next-steps', text=next_steps)
        except IntegrityError:
            pass
        return form_page

    def _create_metadata_collection_form(self, home_page: Page):
        parent = home_page.get_descendants().filter(slug='data-and-resources').first()
        assert parent is not None
        intro = RichText(pkg_resources.resource_string(__name__, 'content/meta-intro.html').decode('utf-8').strip())
        outro = RichText(pkg_resources.resource_string(__name__, 'content/meta-outro.html').decode('utf-8').strip())
        self.stdout.write('📀 Creating the metadata collection form page')
        form_page = MetadataCollectionFormPage(
            title='Metadata Collection Form',
            intro=intro,
            outro=outro,
            from_address='ic-data@jpl.nasa.gov',
            to_address='sean.kelly@jpl.nasa.gov,heather.kincaid@jpl.nasa.gov',
            subject='New Metadata Collection has been submitted'
        )
        parent.add_child(instance=form_page)
        form_page.save()
        return form_page

    def handle(self, *args, **options):
        self.stdout.write('Populating the EDRN site with the new forms')

        old = getattr(settings, 'WAGTAILREDIRECTS_AUTO_CREATE', True)
        try:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = False
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = False
            site, home_page = set_site()

            self.stdout.write('⌦ Deleting any current form pages')
            SpecimenReferenceSetRequestFormPage.objects.all().delete()
            MetadataCollectionFormPage.objects.all().delete()
            self._create_specimen_ref_set_req_form_page(home_page)
            self._create_metadata_collection_form(home_page)

        finally:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = old
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
            self.stdout.write('Job done!')
