# encoding: utf-8

'''🧬 EDRN Site: export site people roles.'''

from django.core.management.base import BaseCommand
from django.db.models import Prefetch
from django.db.models.functions import Lower
from eke.knowledge.models import Person, Site
import csv


class Command(BaseCommand):
    '''Export each site's people roles to a CSV file.'''

    help = 'Export site PIs, co-PIs, co-Is, and investigators to people.csv.'

    def _person_title(self, person) -> str:
        return person.title.strip() if person else ''

    def _people_titles(self, people: list[Person]) -> str:
        titles = [self._person_title(person) for person in people]
        return '|'.join([title for title in titles if title])

    def handle(self, *args, **options):
        '''Handle the EDRN `edrn_site_people` command.'''
        ordered_people = Person.objects.order_by(Lower('title'))
        sites = Site.objects.select_related('pi').prefetch_related(
            Prefetch('coPIs', queryset=ordered_people, to_attr='ordered_coPIs'),
            Prefetch('coIs', queryset=ordered_people, to_attr='ordered_coIs'),
            Prefetch('investigators', queryset=ordered_people, to_attr='ordered_investigators'),
        ).order_by(Lower('memberType'), Lower('title'))

        with open('people.csv', 'w', newline='', encoding='UTF-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(['dmccSiteID', 'site name', 'member type', 'PI', 'co-PIs', 'co-Is', 'investigators'])
            for site in sites:
                writer.writerow([
                    site.dmccSiteID,
                    site.title,
                    site.memberType,
                    self._person_title(site.pi),
                    self._people_titles(site.ordered_coPIs),
                    self._people_titles(site.ordered_coIs),
                    self._people_titles(site.ordered_investigators),
                ])

        self.stdout.write(f'Wrote {sites.count()} sites to people.csv')
