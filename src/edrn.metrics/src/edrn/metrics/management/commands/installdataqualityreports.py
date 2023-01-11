# encoding: utf-8

'''📐 EDRN metrics: data quality reports instantition.'''

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from edrn.metrics.models import ReportIndex, generate_report
from wagtail.models import Site, PageViewRestriction


class Command(BaseCommand):
    '''Install data quality reports.'''

    help = 'Installs data quality reports'

    def handle(self, *args, **options):
        '''Handle the EDRN `installdataqualityreports` command.'''
        site = Site.objects.filter(is_default_site=True).first()
        assert site.site_name == 'Early Detection Research Network'

        site.root_page.get_children().filter(title='Data Quality Reports').delete()
        index = ReportIndex(title='Data Quality Reports', live=True)
        site.root_page.add_child(instance=index)
        pvr = PageViewRestriction(page=index, restriction_type='groups')
        pvr.save()
        pvr.groups.set(Group.objects.filter(name='Super User'), clear=True)
        index.save()
        generate_report(index)
