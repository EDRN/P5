# encoding: utf-8

from django.core.management.base import BaseCommand
from eke.knowledge.models import PublicationIndex
from wagtail.models import Page


class Command(BaseCommand):
    def handle(self, *args, **options):
        folders = PublicationIndex.objects.live().public()
        for folder in folders:
            self.stdout.write(f'Nuking children of {folder.url_path}')
            children = folder.get_children()
            for child in children:
                child.delete()

            folder.refresh_from_db()
            
            self.stdout.write(f'Adding a bunch of pages to {folder.url_path}')
            for item in range(100):
                child = Page(title=f'Title of page {item}')
                folder.add_child(instance=child)
