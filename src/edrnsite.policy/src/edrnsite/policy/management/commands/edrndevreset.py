# encoding: utf-8

'''🧬 EDRN Site: development reset.'''

from django.core.management.base import BaseCommand
from edrnsite.controls.models import Informatics, AnalyticsSnippet
from wagtail.models import Site
from robots.models import Rule, DisallowedUrl


class Command(BaseCommand):
    '''The EDRN development reset command.'''

    help = 'Reset the EDRN P5 portal for use in development'

    def handle(self, *args, **options):
        '''Handle the EDRN `edrndevreset` command.'''
        site = Site.objects.filter(is_default_site=True).first()
        assert site.site_name == 'Early Detection Research Network'

        informatics = Informatics.for_site(site)
        informatics.in_development = True
        informatics.save()

        AnalyticsSnippet.objects.all().delete()

        Rule.objects.filter(sites=site).delete()
        rule = Rule(robot='*')
        rule.save()
        rule.sites.add(site)
        url = DisallowedUrl(pattern='/')
        rule.disallowed.add(url)
        url.save()
        rule.save()
