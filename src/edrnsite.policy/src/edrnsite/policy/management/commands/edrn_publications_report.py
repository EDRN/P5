# encoding: utf-8

'''🧬 EDRN Site: Publications Report.

To support reporting of numbers of publications for the EDRN quarterly report.
'''

from django.core.management.base import BaseCommand
from eke.knowledge.models import Publication


class Command(BaseCommand):
    '''The EDRN publications report command.'''

    help = 'Report on the numbers of publications for the EDRN quarterly report.'

    def handle(self, *args, **options):
        '''Handle the EDRN `edrn_publications_report` command.'''
        dmcc_pubs = Publication.objects.filter(
            subject_uris__identifier__startswith='http://edrn.nci.nih.gov/data/pubs/'
        )
        grant_pubs = Publication.objects.filter(
            subject_uris__identifier__startswith='urn:edrn:knowledge:publication:via-grants:'
        )

        on_page = dmcc_pubs.filter(year__isnull=False).union(grant_pubs.filter(year__isnull=False)).count()
        self.stdout.write(f'Reported on Publications page: {on_page}')
        self.stdout.write('The number on the publications page includes only those from the DMCC and the grant numbers and omits publications without year-of-publication information and omits those from the BMDB.')
        self.stdout.write()

        without_year = dmcc_pubs.union().count()
        self.stdout.write(f'Including publications without a year (and not from BMDB): {without_year}')
        self.stdout.write()

        total = Publication.objects.count()
        self.stdout.write(f'All publications, including those from BMDB: {total}')
