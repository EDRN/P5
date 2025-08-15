# encoding: utf-8

'''🧬 EDRN Site: Biomarker descriptions report.

Generates a CSV containing descriptions of biomarkers for each general
biomarker plus its organ-specific descriptions.
'''

from django.core.management.base import BaseCommand
from eke.biomarkers.models import Biomarker, BiomarkerBodySystem
import csv, sys


class Command(BaseCommand):
    '''Biomarker descriptions report command.'''

    help = 'Report on biomarker descriptions'

    def handle(self, *args, **options):
        '''Handle the EDRN `edrn_biomarker_descriptions` command.'''

        # The names of body systems in BodySystem don't necessarily intersect with those in BiomarkerBodySystem.
        # So let's get the unique values from BiomarkerBodySystem.
        body_systems = list(BiomarkerBodySystem.objects.values_list('title', flat=True).distinct().order_by('title'))

        with open('biomarker_descriptions.csv', 'w') as f:
            writer = csv.writer(f)
            header = ['Biomarker', 'Description'] + [f'{bs} Description' for bs in body_systems]
            writer.writerow(header)

            self.stderr.write(f'Writing {Biomarker.objects.all().count()} biomarkers')

            count = 0
            for biomarker in Biomarker.objects.all().order_by('title'):
                name = biomarker.hgnc_name if biomarker.hgnc_name else biomarker.title
                row = [biomarker.identifier, name]
                if biomarker.description: row.append(biomarker.description)
                else: row.append('«N/A»')

                for bs in body_systems:
                    bbs = BiomarkerBodySystem.objects.filter(title=bs, biomarker=biomarker).first()
                    if bbs is not None:
                        desc, comment = bbs.description, bbs.performance_comment
                        if desc and comment:
                            organ_description = f'Description: «{desc}»; performance comment: «{comment}»'
                        elif desc:
                            organ_description = desc
                        elif comment:
                            organ_description = comment
                        else:
                            organ_description = '«N/A»'
                        row.append(organ_description)
                    else: row.append('«not indicated»')

                self.stderr.write(f'Writing row for {name}')
                writer.writerow(row)
                count += 1

            self.stderr.write(f'Wrote {count} rows')
