# encoding: utf-8

'''🧬 EDRN Site: version command.'''

from django.core.management.base import BaseCommand
from importlib import import_module


class Command(BaseCommand):
    '''The EDRN Version command.'''

    help = 'Tell what version of the EDRN Site Policy (and therefore of the entire EDRN site) is installed here'

    def handle(self, *args, **options):
        '''Handle the EDRN version command by printing our comprised package versions.'''
        from edrnsite.policy import VERSION
        self.stdout.write(f'edrnsite.policy {VERSION}')
        for depName in sorted((
            'edrnsite.controls', 'edrn.theme', 'edrnsite.streams', 'edrnsite.content', 'eke.knowledge',
            'edrnsite.search', 'edrn.collabgroups', 'eke.biomarkers', 'edrnsite.ploneimport', 'edrn.auth',
            'eke.geocoding'
        )):
            module = import_module(depName)
            version = getattr(module, 'VERSION', '«unknown»')
            self.stdout.write(f'{depName} {version}')
