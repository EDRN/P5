# encoding: utf-8

'''🧬 EDRN Site: report people counts by member type.'''

from django.core.management.base import BaseCommand
from eke.knowledge.models import Person, Site


class Command(BaseCommand):
    '''Report people counts by member type.'''

    help = 'Report the number of people in each site by member type.'

    def _get_site(self, person: Person) -> Site | None:
        parent = person.get_parent().specific
        return parent if isinstance(parent, Site) else None

    def handle(self, *args, **options):
        '''Handle the EDRN `edrn_people_counts` command.'''
        counts = {}
        for person in Person.objects.order_by('title'):
            site = self._get_site(person)
            if site is None:
                self.stderr.write(f'Person {person.title} does not belong to a site; skipping')
                continue
            counts[site.memberType] = counts.get(site.memberType, 0) + 1

        for member_type, count in sorted(counts.items(), key=lambda item: item[0].lower()):
            self.stdout.write(f'{member_type}: {count}')
