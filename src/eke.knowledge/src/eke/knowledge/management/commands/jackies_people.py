# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: Jackie Dahlgren's special request.'''


from django.core.management.base import BaseCommand
from eke.knowledge.models import Person
from django.db.models.functions import Lower
import csv, argparse, sys


class Command(BaseCommand):
    help = "Produce Jackie Dahlgren's special report on people in the portal"

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-csv', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
            help='Where to write the CSV file, defaults to stdout'
        )

    def handle(self, *args, **options):
        people = Person.objects.all().order_by(Lower('title'))
        writer = csv.writer(options['output_csv'])
        for person in people:
            writer.writerow((person.personID, person.title))
        options['output_csv'].close()
