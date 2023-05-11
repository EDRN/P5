# encoding: utf-8

'''📐 EDRN Metrics: models.'''


from .utils import (
    find_pubs_without_pis, find_data_without_biomarkers, find_data_collections_without_pis,
    find_biomarkers_without_publications, find_biomarkers_without_data
)
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from eke.biomarkers.models import Biomarker
from eke.knowledge.models import DataCollection, Publication
from modelcluster.fields import ParentalManyToManyField
from wagtail.models import Page
from django.utils import timezone


class DataQualityReport(Page):
    template = 'edrn.metrics/data-quality-report.html'
    page_description = 'A report on data quality within the portal'
    parent_page_types = ['edrnmetrics.ReportIndex']
    publess_biomarkers = ParentalManyToManyField(
        Biomarker, blank=True, verbose_name='Biomarkers without publications', related_name='dqr_publess'
    )
    dataless_biomarkers = ParentalManyToManyField(
        Biomarker, blank=True, verbose_name='Biomarkers without science data', related_name='dqr_dataless'
    )
    piless_data = ParentalManyToManyField(
        DataCollection, blank=True, verbose_name='Data collections without PIs', related_name='dqr_piless'
    )
    biomarkerless_data = ParentalManyToManyField(
        DataCollection, blank=True, verbose_name='Data collections without biomarkers', related_name='dqr_biomarkerless'
    )
    piless_pubs = ParentalManyToManyField(
        Publication, blank=True, verbose_name='Publications without PIs', related_name='dqr_pubs'
    )
    def get_context(self, request: HttpRequest, *args, **kwargs) -> dict:
        context = super().get_context(request, args, kwargs)
        context['publess_biomarkers'] = self.publess_biomarkers.all().order_by('title')
        context['dataless_biomarkers'] = self.dataless_biomarkers.all().order_by('title')
        context['piless_data'] = self.piless_data.all().order_by('title')
        context['biomarkerless_data'] = self.biomarkerless_data.all().order_by('title')
        context['piless_pubs'] = self.piless_pubs.all().order_by('title')
        return context


class ReportIndex(Page):
    template = 'edrn.metrics/report-index.html'
    search_auto_update = False
    subpage_types = [DataQualityReport]
    page_description = 'Container for data quality reports'

    def serve(self, request: HttpRequest) -> HttpResponse:
        if request.GET.get('new') == 'true':
            return HttpResponseRedirect(generate_report(self).url)
        else:
            return super().serve(request)

    def get_context(self, request: HttpRequest, *args, **kwargs) -> dict:
        context = super().get_context(request, args, kwargs)
        reports = DataQualityReport.objects.child_of(self).live().order_by('-title')

        if reports.count() == 0:
            publess_biomarkers = dataless_biomarkers = piless_data = biomarkerless_data = piless_pubs = '?'
        else:
            latest              = reports[0]
            publess_biomarkers  = latest.publess_biomarkers.count()
            dataless_biomarkers = latest.dataless_biomarkers.count()
            piless_data         = latest.piless_data.count()
            biomarkerless_data  = latest.biomarkerless_data.count()
            piless_pubs         = latest.piless_pubs.count()

        context['publess_biomarkers']  = publess_biomarkers
        context['dataless_biomarkers'] = dataless_biomarkers
        context['piless_data']         = piless_data
        context['biomarkerless_data']  = biomarkerless_data
        context['piless_pubs']         = piless_pubs
        context['reports']             = reports

        return context


def generate_report(index: ReportIndex) -> DataQualityReport:
    when = timezone.now()
    dqr = DataQualityReport(title=when.isoformat(sep=' ', timespec='minutes'), live=True)
    index.add_child(instance=dqr)

    report = find_biomarkers_without_publications()
    dqr.publess_biomarkers.set(report)
    dqr.save()
    del report

    report = find_biomarkers_without_data()
    dqr.dataless_biomarkers.set(report)
    dqr.save()
    del report

    report = find_data_collections_without_pis()
    dqr.piless_data.set(report)
    dqr.save()
    del report

    report = find_data_without_biomarkers()
    dqr.biomarkerless_data.set(report)
    dqr.save()
    del report

    report = find_pubs_without_pis()
    dqr.piless_pubs.set(report)
    dqr.save()
    del report

    return dqr
