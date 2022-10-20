# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: Jackie Dahlgren's special request.'''


from django.core.management.base import BaseCommand
from eke.knowledge.models import Person, Site
from django.db.models.functions import Lower
import csv, argparse, sys


class Command(BaseCommand):
    help = "Produce Jackie Dahlgren's special report on people in the portal"

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-csv', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
            help='Where to write the CSV file, defaults to stdout'
        )
        parser.add_argument('--site-id', type=int, help='Limit report to one site ID')

    def handle(self, *args, **options):
        if options['site_id']:
            people = Site.objects.filter(dmccSiteID=options['site_id']).first().get_children().order_by(Lower('title')).specific()
        else:
            people = Person.objects.all().order_by(Lower('title'))
        writer = csv.writer(options['output_csv'])
        for person in people:
            writer.writerow((person.personID, person.title))
        options['output_csv'].close()
