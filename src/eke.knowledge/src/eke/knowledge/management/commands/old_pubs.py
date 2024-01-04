# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: PubMed paper retreival.'''

from django.core.management.base import BaseCommand
from eke.knowledge.models import Publication, PublicationSubjectURI
import logging, csv


class Command(BaseCommand):
    help = 'Find all old publications given only by the DMCC'

    def handle(self, *args, **options):
        verbosity = int(options['verbosity'])
        root_logger = logging.getLogger('')
        if verbosity >= 3:
            root_logger.setLevel(logging.DEBUG)

        with open('old-pubs-no-bmdb.csv', 'w', newline='', encoding='utf-8') as io:
            writer = csv.writer(io)
            writer.writerow(['PubMed ID', 'Title', 'Year'])
            for pub in Publication.objects.filter(year__lt=2000):
                results = PublicationSubjectURI.objects.filter(page=pub)
                count = results.filter(identifier__startswith='http://edrn.jpl.nasa.gov/bmdb').count()
                if count == 0:
                    writer.writerow([pub.pubMedID, pub.title, pub.year])
