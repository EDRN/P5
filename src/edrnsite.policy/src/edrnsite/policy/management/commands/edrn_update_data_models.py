# encoding: utf-8

'''🧬 EDRN Site: update data models from Google Drive.'''

from django.core.management.base import BaseCommand
from edrnsite.streams.views import update_data_element_explorer_trees
import logging


class Command(BaseCommand):
    help = 'Updates all data models with contents from Google Drive'

    def handle(self, *args, **options):
        verbosity = int(options['verbosity'])
        root_logger = logging.getLogger('')
        if verbosity >= 3:
            root_logger.setLevel(logging.DEBUG)

        self.stdout.write('Updating data models')
        results = update_data_element_explorer_trees()
        if verbosity >= 3:
            self.stdout.write('Results:')
            for line in results:
                self.stdout.write(line.strip())
        self.stdout.write(self.style.SUCCESS('🎉 Done!'))
