# encoding: utf-8

'''📐 EDRN Metrics: tests for report generation.'''


from edrn.metrics.models import DataQualityReport, ReportIndex, generate_report
from wagtail.models import Site as WagtailSite
from wagtail.test.utils import WagtailPageTestCase
from wagtail.test.utils.form_data import nested_form_data


class ReportGenerationTest(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root_page = WagtailSite.objects.filter(is_default_site=True).first().root_page
        cls.report_index = ReportIndex(title='Test Reports')
        cls.root_page.add_child(instance=cls.report_index)
        cls.report_index.save()

    def setUp(self):
        self.login()

    def test_empty_report(self):
        '''Ensure that if there's noting in the knowledge environment that the report shows zero problems.'''

        dqr = generate_report(self.report_index)

        self.assertEqual(0, dqr.publess_biomarkers.count())
        self.assertEqual(0, dqr.dataless_biomarkers.count())
        self.assertEqual(0, dqr.piless_data.count())
        self.assertEqual(0, dqr.biomarkerless_data.count())
        self.assertEqual(0, dqr.piless_pubs.count())

    def test_full_report(self):
        '''Ensure that if there are problems in the knowledge environment that the report indicates issues.'''
        pass
