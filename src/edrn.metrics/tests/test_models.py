# encoding: utf-8

'''📐 EDRN Metrics: tests for the Django models.'''


from edrn.metrics.models import DataQualityReport, ReportIndex
from wagtail.models import Site as WagtailSite
from wagtail.test.utils import WagtailPageTestCase
from wagtail.test.utils.form_data import nested_form_data


class ReportIndexTest(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root_page = WagtailSite.objects.filter(is_default_site=True).first().root_page

    def setUp(self):
        self.login()

    def test_model_location(self):
        '''Ensure report indexes can be created anywhere.'''
        from edrnsite.content.models import HomePage
        self.assertCanCreateAt(HomePage, ReportIndex)

    def test_model_creation(self):
        '''Ensure we can instantiate a report index.'''
        self.assertCanCreate(self.root_page, ReportIndex, nested_form_data({'title': 'My Report Index'}))


class DataQualityReportTest(WagtailPageTestCase):
    def setUp(self):
        self.login()

    def test_model_location(self):
        '''Ensure data quality reports can only be created in report indexes.'''
        from edrnsite.content.models import HomePage
        self.assertCanNotCreateAt(HomePage, DataQualityReport)
        self.assertCanCreateAt(ReportIndex, DataQualityReport)

    def test_model_creation(self):
        '''Esnure data quality reports can be instantiated.'''
        index = ReportIndex(title='My Report Index')
        WagtailSite.objects.filter(is_default_site=True).first().root_page.add_child(instance=index)
        index.save()
        self.assertCanCreate(index, DataQualityReport, nested_form_data({'title': 'My Data Quality Report'}))
