# encoding: utf-8

'''😌 EDRN Site Content: remove old explorer, create new one.'''

from django.conf import settings
from django.core.management.base import BaseCommand
from edrnsite.content.models import FlexPage
from edrnsite.policy.management.commands.utils import set_site
from edrnsite.streams.views import update_data_element_explorer_trees
from wagtail.models import Page
from wagtail.rich_text import RichText


_help_html = '''<p>To use the data models:</p>
<ul>
<li>Click/tap on the triangle icon to the left of each section to expand and view its contents.</li>
<li>Click/tap on the text within a section to access detailed information about the model, including its specific attributes and details.</li>
</ul>'''

_faq_html = '''<p>For questions about the data models, <a href="mailto:ic-portal@jpl.nasa.gov">email
the Informatics Center</a>.'''


class Command(BaseCommand):
    help = 'Replace old CDE viewer page with new block-based explorer flex page'

    def _update_cde_explorer(self, home_page):
        # There should be just one current CDEExplorerPage
        count = Page.objects.filter(slug='edrn-data-model').count()
        if count > 1:
            raise ValueError("There's more than one edrn-data-model! Not sure what to do")
        elif count == 0:
            self.stdout.write('No edrn-data-model found, so using existing "cde" page as the parent')
            parent = FlexPage.objects.filter(slug='cde').first()
            assert parent is not None
        else:
            self.stdout.write('Found the one edrn-data-model, deleting it')
            page = Page.objects.filter(slug='edrn-data-model').first()
            parent = page.get_parent()
            page.delete()
            parent.refresh_from_db()

        self.stdout.write('Creating new EDRN Data Model page')
        page = FlexPage(title='EDRN Data Model', slug='edrn-data-model', show_in_menus=False)
        parent.add_child(instance=page)

        page.body.append(('rich_text', RichText(_help_html)))
        page.body.append(('data_explorer', {
            'title': 'Biomarker Data Models',
            'block_id': 'bio', 'spreadsheet_id': '1Kjkvi-bF5GNpAzvq4Kq6r4g1WpceIyP0Srs2OHJJtGs', 
        }))
        page.body.append(('data_explorer', {
            'title': 'Cancer Biomarker Data Commons (LabCAS) Data Model',
            'block_id': 'lab', 'spreadsheet_id': '1btbwoROmVbZlzSLBn3DQ_6rakZ48j24p-NoOkI3OCFg'
        }))
        page.body.append(('rich_text', RichText(_faq_html)))
        page.save()
        update_data_element_explorer_trees()

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
