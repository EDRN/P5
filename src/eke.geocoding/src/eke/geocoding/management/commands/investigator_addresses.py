# encoding: utf-8

'''🗺 EDRN Knowledge Environment: management command for investigator addresses.'''

from django.core.management.base import BaseCommand
from eke.geocoding.models import InvestigatorAddress
import importlib.resources, csv, argparse, sys, codecs


class Command(BaseCommand):
    help = 'Import or export investigator address data'

    def add_arguments(self, parser: argparse.ArgumentParser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--import', action='store_true', help='Import addresses')
        group.add_argument('--export', action='store_true', help='Export addresses')
        parser.add_argument('--file', help='Optional file to import from or export to')

    def _import(self, filename: str):
        if filename:
            source = open(filename, newline='')
        else:
            reader = codecs.getreader('utf-8')
            source = reader(importlib.resources.resource_stream(__name__, 'ia.csv'))
        try:
            InvestigatorAddress.objects.all().delete()
            reader = csv.reader(source)
            for address, lat, lon in reader:
                ia, _ = InvestigatorAddress.objects.get_or_create(address=address, defaults=dict(lat=lat, lon=lon))
                ia.save()
        finally:
            source.close()

    def _export(self, filename: str):
        output = sys.stdout if filename is None else open(filename, 'w', newline='')
        try:
            writer = csv.writer(output)
            for ia in InvestigatorAddress.objects.all():
                writer.writerow((ia.address, ia.lat, ia.lon))
        finally:
            output.close()

    def handle(self, *args, **options):
        if options['import']:
            self._import(options['file'])
        elif options['export']:
            self._export(options['file'])
        else:
            raise ValueError("Either --import or --export should've been specified")
