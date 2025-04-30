# encoding: utf-8

'''🧬 EDRN Site: audit log.'''

from django.core.management.base import BaseCommand
from wagtail.models import PageLogEntry


class Command(BaseCommand):
    '''The EDRN "audit log" command".'''

    help = 'Cleans up audit log entries with no users'

    def handle(self, *args, **options):
        '''Handle the EDRN `edrn audit log` command.'''

        self.stdout.write('Removing all PageLogEntry audits with no recorded user; this can take a while')
        PageLogEntry.objects.filter(user__isnull=True).delete()
        self.stdout.write('All done, wooo let us dance 💃')

        # 🔮 TODO: should we also purge old log entries?