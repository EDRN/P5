# encoding: utf-8

'''😌 EDRN Site Content: create new forms.'''

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from edrnsite.policy.management.commands.utils import set_site
from html.parser import HTMLParser
from io import StringIO
from wagtail.documents.models import Document
from wagtail.models import Page
from wagtail.rich_text import RichText
from edrnsite.content.models import (
    SpecimenReferenceSetRequestFormPage, MetadataCollectionFormPage, BoilerplateSnippet, FlexPage
)
import pkg_resources


class _SpecRefSetLinkFixer(HTMLParser):
    def __init__(self, old_doc, new_page):
        super().__init__()
        self.old_doc, self.new_page = str(old_doc), str(new_page)
        self._buffer = StringIO()

    def get_fixed(self):
        return self._buffer.getvalue()

    def _format_starttag(self, tag, attrs, empty):
        if not attrs:
            return f'<{tag}/>' if empty else f'<{tag}>'
        start = f'<{tag} '
        middle = []
        for key, value in attrs:
            middle.append(f'{key}="{value}"')
        middle = ' '.join(middle)
        end = '/>' if empty else '>'
        return start + middle + end

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            d = {k: v for k, v in attrs}
            if d.get('linktype') == 'document' and d.get('id') == self.old_doc:
                attrs = [('id', self.new_page), ('linktype', 'page')]
        self._buffer.write(self._format_starttag(tag, attrs, empty=False))

    def handle_endtag(self, tag):
        self._buffer.write(f'</{tag}>\n')

    def handle_startendtag(self, tag, attrs):
        self._buffer.write(self._format_starttag(tag, attrs, empty=True))

    def handle_data(self, data):
        self._buffer.write(data)


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

    def _link_spec_ref_set_req_form(self, form: Page):
        old_doc = Document.objects.filter(title='EDRN General Reference Set Application').first()
        assert old_doc is not None
        old_doc_id = old_doc.pk
        slugs = (
            'breast-cancer-reference-sets',
            'colon-cancer-reference-sets',
            'liver-hepatocellular-carcinoma-reference-set',
            'lung-cancer-reference-sets',
            'pancreatic-standard-specimen-reference-set',
            'protstate-reference-sets',
            'pancreatic-standard-specimen-reference-set',
        )
        for page in FlexPage.objects.filter(slug__in=slugs):
            if len(page.body) != 1: continue
            if page.body[0].block_type != 'rich_text': continue
            original = page.body[0].value.source
            del page.body[0]
            self.stdout.write(f'Making new link to spec ref set app form on page "{page.title}"')
            fixer = _SpecRefSetLinkFixer(old_doc_id, form.pk)
            fixer.feed(original)
            fixer.close()
            page.body.append(('rich_text', RichText(fixer.get_fixed())))
            page.save()

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
            spec_ref_set_req_form = self._create_specimen_ref_set_req_form_page(home_page)
            self._create_metadata_collection_form(home_page)
            self._link_spec_ref_set_req_form(spec_ref_set_req_form)

        finally:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = old
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
            self.stdout.write('Job done!')
