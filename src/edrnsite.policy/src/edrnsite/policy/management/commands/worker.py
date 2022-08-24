# encoding: utf-8

'''🧬 EDRN Site: Celery worker startup.'''

from django.conf import settings
from django.core.management.base import BaseCommand
import os, sys


class Command(BaseCommand):
    help = 'Start a Celery worker with Django settings'

    _log_levels = {
        0: 'ERROR',
        1: 'WARNING',
        2: 'INFO',
        3: 'DEBUG',
    }

    def handle(self, *args, **options):
        self.stdout.write('Starting worker')

        os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings.SETTINGS_MODULE)
        # See https://cutt.ly/bGBgSDz or https://cutt.ly/QGBhcyl
        os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'yes'

        pydir = os.path.dirname(sys.executable)
        path = pydir + os.pathsep + os.environ.get('PATH', '.')
        os.environ['PATH'] = path
        args = [
            'celery', '--no-color', '--app', 'edrnsite.policy',
            'worker',
            '--hostname', 'worker', '--loglevel', self._log_levels[options['verbosity']]
        ]
        self.stdout.flush()
        os.execvp('celery', args)
