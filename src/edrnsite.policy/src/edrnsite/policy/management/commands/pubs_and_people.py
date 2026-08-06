# encoding: utf-8

'''🧬 EDRN Site: Publications and people CSV report.

Match publication authors to Person objects and emit one CSV row per author
per publication.
'''

from django.core.management.base import BaseCommand, CommandError
from django.http import HttpRequest, QueryDict
from eke.knowledge.models import Person, PublicationIndex
import argparse, csv, sys


class Command(BaseCommand):
    '''CSV report of publication authors matched to portal Person pages.'''

    help = (
        'Produce a CSV of DMCC/grant publications with each author and, when '
        'found, the matching Person RDF identifier and portal URL.'
    )

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            'outfile', help='Output CSV file, defaults to stdout', default=sys.stdout, nargs='?',
            type=argparse.FileType(mode='w', encoding='UTF-8')
        )
        parser.add_argument(
            '--base-url', default='https://edrn.cancer.gov',
            help='Base URL prepended to Person page paths (default: https://edrn.cancer.gov)'
        )

    def _author_key(self, author_name: str) -> tuple[str, str] | None:
        '''Turn a PubMed-style author name ("Last Initials") into a lookup key.'''
        parts = author_name.strip().split()
        if not parts:
            return None
        last = parts[0].rstrip(',').lower()
        initials = parts[1].upper() if len(parts) > 1 else ''
        return last, initials

    def _person_key(self, title: str) -> tuple[str, str] | None:
        '''Turn a Person title ("Last, First Middle") into a lookup key.'''
        title = title.strip()
        if not title or title.startswith('«'):
            return None
        if ',' in title:
            last, given = title.split(',', 1)
            last = last.strip().lower()
            initials = ''.join(word[0] for word in given.strip().split() if word).upper()
            return last, initials
        return title.lower(), ''

    def _build_person_index(self) -> dict[tuple[str, str], Person]:
        '''Index live public people by (last name, initials) for author lookup.'''
        index: dict[tuple[str, str], Person] = {}
        for person in Person.objects.live().public():
            key = self._person_key(person.title)
            if key is None or key in index:
                continue
            index[key] = person
        return index

    def _find_person(self, author_name: str, people: dict[tuple[str, str], Person]) -> Person | None:
        '''Find the Person matching a publication author name, if any.'''
        key = self._author_key(author_name)
        if key is None:
            return None
        person = people.get(key)
        if person is not None:
            return person

        # Allow prefix agreement on initials when formats differ slightly
        # (e.g. author "Smith J" vs person "Smith, John A" → JA).
        last, initials = key
        if not initials:
            return None
        matches = [
            candidate
            for (person_last, person_initials), candidate in people.items()
            if person_last == last and person_initials and (
                person_initials.startswith(initials) or initials.startswith(person_initials)
            )
        ]
        if len(matches) == 1:
            return matches[0]
        return None

    def handle(self, *args, **options):
        '''Handle the EDRN `pubs_and_people` command.'''
        count = PublicationIndex.objects.count()
        if count == 0:
            raise CommandError('No publication index found')
        if count > 1:
            raise CommandError('Multiple publication indexes found which should not happen')

        publication_index = PublicationIndex.objects.first()
        request = HttpRequest()
        request.GET = QueryDict()
        publications = publication_index.get_contents(request)
        people = self._build_person_index()
        base_url = options['base_url'].rstrip('/')

        rows = 0
        with options['outfile'] as outfile:
            writer = csv.writer(outfile)
            writer.writerow([
                'Publication RDF Identifier',
                'Publication URL on the Portal',
                'Publication Title',
                'PubMed ID',
                'Author from PubMed API',
                'Possibly matching Person RDF Identifier',
                'Possibly matching Person URL on the Portal',
            ])
            for publication in publications:
                for author in publication.authors.all():
                    person = self._find_person(author.value, people)
                    person_url = f'{base_url}{person.url}' if person and person.url else ''
                    publication_url = f'{base_url}{publication.url}' if publication.url else ''
                    writer.writerow([
                        publication.identifier,
                        publication_url,
                        publication.title,
                        publication.pubMedID,
                        author.value,
                        person.identifier if person else '',
                        person_url,
                    ])
                    rows += 1

        self.stderr.write(self.style.SUCCESS(f'Wrote {rows} author rows'))
