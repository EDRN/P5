# encoding: utf-8

from django.core.management.base import BaseCommand
from eke.knowledge.models import PublicationIndex
from wagtail.models import Page
# from wagtail.management.commands.fixtree import Command as FixtreeCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        folders = PublicationIndex.objects.live().public()
        for folder in folders:
            self.stdout.write(f'Adding a bunch of pages to {folder.url_path}')
            for item in range(100):
                child = Page(title=f'Title of page {item}')
                folder.add_child(instance=child)
