# encoding: utf-8

'''🧬 EDRN Site: Publications Report.

To support reporting of numbers of publications for the EDRN quarterly report.
'''

from django.core.management.base import BaseCommand
from django.db.models import Q
from eke.knowledge.models import Publication
import argparse, csv


class Command(BaseCommand):
    '''The EDRN publications report command.'''

    help = 'Report on the numbers of publications for the EDRN quarterly report.'

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            '--csv', metavar='FILE', nargs='?', const='-', default=None,
            help=(
                'Write a CSV of all DMCC and grant publications (one row per Publication). '
                'Omit FILE or use - to write to stdout.'
            ),
        )
        parser.add_argument(
            '--correlate', metavar='FILE', nargs='?', default=None,
            help=(
                'Read FILE of PubMedIDs and write a report of which are found in DMCC, which in grant numbers, '
                'and which are missing'
            )
        )

    def _dmcc_and_grant_pubs(self):
        '''Return DMCC and grant-number Publication querysets.'''
        dmcc_pubs = Publication.objects.filter(
            subject_uris__identifier__startswith='http://edrn.nci.nih.gov/data/pubs/'
        )
        grant_pubs = Publication.objects.filter(
            subject_uris__identifier__startswith='urn:edrn:knowledge:publication:via-grants:'
        )
        return dmcc_pubs, grant_pubs

    def _write_csv(self, outfile):
        '''Write one CSV row per DMCC/grant Publication.'''
        pubs = Publication.objects.filter(
            Q(subject_uris__identifier__startswith='http://edrn.nci.nih.gov/data/pubs/') |
            Q(subject_uris__identifier__startswith='urn:edrn:knowledge:publication:via-grants:')
        ).distinct().prefetch_related('authors').order_by('identifier')

        writer = csv.writer(outfile)
        writer.writerow([
            'identifier', 'pubMedID', 'title', 'authors', 'issue', 'volume',
            'journal', 'year', 'month'
        ])
        rows = 0
        for publication in pubs:
            authors = '|'.join(a.value for a in publication.authors.all())
            writer.writerow([
                publication.identifier,
                publication.pubMedID,
                publication.title,
                authors,
                publication.issue,
                publication.volume,
                publication.journal,
                publication.year if publication.year is not None else '',
                publication.month,
            ])
            rows += 1
        return rows

    def _checkmark(self, value):
        '''Return a checkmark or an empty string.'''
        return '✓' if value else ''

    def handle(self, *args, **options):
        '''Handle the EDRN `edrn_publications_report` command.'''
        if options['csv'] is not None:
            path = options['csv']
            if path == '-':
                rows = self._write_csv(self.stdout)
                self.stderr.write(self.style.SUCCESS(f'Wrote {rows} publication rows'))
            else:
                with open(path, 'w', encoding='UTF-8', newline='') as outfile:
                    rows = self._write_csv(outfile)
                self.stdout.write(self.style.SUCCESS(f'Wrote {rows} publication rows to {path}'))
            return

        dmcc_pubs, grant_pubs = self._dmcc_and_grant_pubs()

        if options['correlate'] is not None:
            results = []
            with open(options['correlate'], 'r', encoding='UTF-8') as infile:
                for line in infile:
                    pubmed_id = line.strip()
                    if pubmed_id:
                        dmcc, grant = dmcc_pubs.filter(pubMedID=pubmed_id).first(), grant_pubs.filter(pubMedID=pubmed_id).first()
                        found_in_dmcc, found_in_grant = dmcc is not None, grant is not None
                        results.append((pubmed_id, found_in_dmcc, found_in_grant))
            writer = csv.writer(self.stdout)
            writer.writerow(['pubMedID', 'Pub found in DMCC SOAP API', 'Pub found in EDRN grant numbers'])
            for result in results:
                writer.writerow((result[0], self._checkmark(result[1]), self._checkmark(result[2])))

        on_page = dmcc_pubs.filter(year__isnull=False).union(grant_pubs.filter(year__isnull=False)).count()
        self.stdout.write(f'Reported on Publications page: {on_page}')
        self.stdout.write('The number on the publications page includes only those from the DMCC and the grant numbers and omits publications without year-of-publication information and omits those from the BMDB.')
        self.stdout.write()

        without_year = dmcc_pubs.union().count()
        self.stdout.write(f'Including publications without a year (and not from BMDB): {without_year}')
        self.stdout.write()

        total = Publication.objects.count()
        self.stdout.write(f'All publications, including those from BMDB: {total}')
