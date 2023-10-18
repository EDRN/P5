# encoding: utf-8

'''😌 EDRN Site Content: nuke photos.'''

from django.conf import settings
from django.core.management.base import BaseCommand
from wagtail.images.models import Image


class Command(BaseCommand):
    help = 'Delete specific instances of duplicate photos'

    _to_nuke = (
        'Photo of Chinnaiyan',
        'Photo of Feng',
        'Photo of Hanash',
        'Photo of Semmes',
        'Photo of Srivastava',
        'Photo of Stass',
    )

    def nuke_photos(self):
        for title in self._to_nuke:
            count = Image.objects.filter(title=title).count()
            if count > 0:
                self.stdout.write(f'Deleting {count} instance(s) of {title}')
                Image.objects.filter(title=title).delete()

    def handle(self, *args, **options):
        self.stdout.write('Deleting specific instances of duplicate photos')

        old = getattr(settings, 'WAGTAILREDIRECTS_AUTO_CREATE', True)
        try:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = False
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = False
            self.nuke_photos()
        finally:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = old
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
            self.stdout.write("Job's done!")
