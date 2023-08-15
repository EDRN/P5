# encoding: utf-8

'''😌 EDRN Site Content: create new forms.'''

from django.conf import settings
from django.core.management.base import BaseCommand
from edrnsite.policy.management.commands.utils import set_site
from edrnsite.content.models import ReferenceSetSnippet, SpecimenTypeSnippet
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Makes specimen reference set request form use dynamic data'

    def install_snippets(self):
        self.stdout.write('Creating Reference Set snippets')
        for label in (
            'Benign Breast Disease',
            'Breast Reference Set and Imaging',
            'Cancers in women—BRSCW',
            'Colon Cancer',
            'DCP/Liver Rapid set',
            'DCP/Liver Validation set',
            'Lung Ref Set A Phase 2 Validation (Retrospective)',
            'Lung Ref Set B (Retrospective)',
            'MSA/bladder',
            'Panc Cyst',
            'Pancreatic cancer',
            'Prostate cancer (from PCA3)',
            'LTP2'
        ):
            ReferenceSetSnippet.objects.get_or_create(reference_set_code=slugify(label), label=label)

        self.stdout.write('Creating Specimen Type snippets')
        for label in (
            'Buffy Coat',
            'Cystic Fluid',
            'Data only',
            'Imaging',
            'Plasma',
            'Serum',
            'Stool',
            'Tissue',
            'Urine',
        ):
            SpecimenTypeSnippet.objects.get_or_create(specimen_type_code=slugify(label), label=label)

    def handle(self, *args, **options):
        self.stdout.write('Adding snippets for Specimen Reference Set form')

        old = getattr(settings, 'WAGTAILREDIRECTS_AUTO_CREATE', True)
        try:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = False
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = False
            site, home_page = set_site()
            self.install_snippets()
        finally:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = old
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
            self.stdout.write("Job's done!")
