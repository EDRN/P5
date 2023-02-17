# encoding: utf-8

'''🧬 EDRN Site: search promotions.'''

from django.core.management.base import BaseCommand
from eke.biomarkers.models import Biomarker
from eke.knowledge.models import Site, Protocol, Publication, DataCollection
from wagtail.contrib.search_promotions.models import SearchPromotion
from wagtail.search.models import Query


class Command(BaseCommand):
    '''The EDRN "promote search" command".'''

    help = 'Promotes various search results'

    def handle(self, *args, **options):
        '''Handle the EDRN `edrnpromotesearch` command.'''

        self.stdout.write('Promoting searches of the biomarkers')
        for biomarker in Biomarker.objects.all():
            names = {
                biomarker.hgnc_name, biomarker.hgnc_name.lower(), biomarker.title, biomarker.title.lower()
            }
            for name in names:
                name = name.strip()
                if not name: continue
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
                        del promotion
                except Exception:
                    pass
        self.stdout.write('Setting search descriptions for sites')
        for site in Site.objects.all():
            promotion = f'{site.title} is a site belonging to the Early Detection Research Network.'
            site.search_description = promotion
            site.save()
            del site
        self.stdout.write('Setting search descriptions for protocols')
        for protocol in Protocol.objects.all():
            promotion = f'"{protocol.title}" is a protocol, project, or study that is being pursued or was pursued by the Early Detection Research Network.'
            protocol.search_description = promotion
            protocol.save()
            del protocol
        self.stdout.write('Setting search descriptions for data collections')
        for dc in DataCollection.objects.all():
            promotion = f'"{dc.title}" is scientific data collected by Early Detection Research Network.'
            dc.search_description = promotion
            dc.save()
            del dc

        # This is the wrong place for this, but I don't want to make yet another management command.
        # This is to address bad data in publications as a result of EDRN/P5#228
        self.stdout.write('Okay, this next step can take a long time, do not panic: deleting all publications')
        Publication.objects.all().delete()
        self.stdout.write('All done, wooo 💃')
