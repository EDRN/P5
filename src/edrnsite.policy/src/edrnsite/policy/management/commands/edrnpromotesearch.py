# encoding: utf-8

'''🧬 EDRN Site: search promotions.'''

from django.core.management.base import BaseCommand
from eke.biomarkers.models import Biomarker
from wagtail.contrib.search_promotions.models import SearchPromotion
from wagtail.search.models import Query


class Command(BaseCommand):
    '''The EDRN "promote search" command".'''

    help = 'Promotes biomarkers as search results'

    def handle(self, *args, **options):
        '''Handle the EDRN `edrndevreset` command.'''
        for biomarker in Biomarker.objects.exclude(hgnc_name__exact=''):
            names = {
                biomarker.hgnc_name, biomarker.hgnc_name.lower(), biomarker.title, biomarker.title.lower()
            }
            for name in names:
                try:
                    desc = biomarker.description
                    if not desc:
                        desc = f'This is the recommended biomarker for {name}'
                    query, _ = Query.objects.get_or_create(query_string=name)
                    promotion, created = SearchPromotion.objects.get_or_create(
                        query=query, page=biomarker, defaults={'description': desc}
                    )
                    if created:
                        self.stdout.write(f'Promoting search for {name} to {biomarker}')
                except Exception:
                    pass
