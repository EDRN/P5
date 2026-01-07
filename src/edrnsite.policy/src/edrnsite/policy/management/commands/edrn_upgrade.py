# encoding: utf-8

'''🧬 EDRN Site: Upgrade.'''

from edrnsite.policy import VERSION
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    '''The EDRN upgrade command.'''

    help = 'Upgrades the EDRN site; this changes depending on the release to which the site is being upgraded'

    def handle(self, *args, **options):
        '''Handle the EDRN upgrade command.'''
        self.stdout.write(f'🆙 Upgrading EDRN site to version {VERSION}')

        # For 6.21.0, we add the forbidden publications to the site
        self.stdout.write('🔍 Adding forbidden publications to the site')
        call_command('edrn_forbidden_pubs')

        self.stdout.write("🎉 Job's done!")
