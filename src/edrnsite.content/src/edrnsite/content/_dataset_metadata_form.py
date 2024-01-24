# encoding: utf-8

from .base_forms import (
    AbstractEDRNForm, pi_choices, institution_choices, discipline_choices, data_category_choices, ALL_USERS_DN
)
from .base_models import AbstractFormPage
from captcha.fields import ReCaptchaField
from configparser import ConfigParser
from django import forms
from django.conf import settings
from eke.knowledge.models import DataCollection, Person, Site
from io import StringIO
from urllib.parse import urlparse
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.contrib.forms.models import EmailFormMixin


def _collections():
    return [(i.identifier, i.title) for i in DataCollection.objects.all().order_by('title')]


def _assays():
    return (
        ('DNA-Seq', 'DNA-Seq'),
        ('H-and-E', 'H&E'),
        ('IHC', 'IHC'),
        ('mIHC', 'mIHC'),
        ('RNA-Seq (SMART-3SEQ)', 'RNA-Seq (SMART-3SEQ)'),
        ('RNA-Seq', 'RNA-Seq'),
        ('Single-cell Seq', 'Single-cell Seq'),
        ('WES', 'WES'),
        ('Not Applicable', 'N/A'),
    )


def _content_types():
    return (
        ('Ancillary Data', 'Ancillary Data'),
        ('Biospecimen', 'Biospecimen'),
        ('Clinical', 'Clinical'),
        ('Documentation', 'Documentation'),
        ('Instrument Output', 'Instrument Output'),
        ('Metadata', 'Metadata'),
        ('SOP', 'SOP'),
        ('Summary', 'Summary', ),
    )


def _specimen_types():
    return (
        ('Ascites', 'Ascites'),
        ('Biliary washing/brushing', 'Biliary washing/brushing'),
        ('Blood', 'Blood'),
        ('Bone marrow', 'Bone marrow'),
        ('Bronchial washing/brushing', 'Bronchial washing/brushing'),
        ('Buccal swab/scraping', 'Buccal swab/scraping'),
        ('Cerebrospinal fluid', 'Cerebrospinal fluid'),
        ('Cervical swab/scraping', 'Cervical swab/scraping'),
        ('Ductal lavage aspirate', 'Ductal lavage aspirate'),
        ('Endocervical secretion/mucous', 'Endocervical secretion/mucous'),
        ('Nipple aspirate/discharge', 'Nipple aspirate/discharge'),
        ('Not Applicable', 'Not Applicable'),
        ('Pancretic washing/brushing', 'Pancretic washing/brushing'),
        ('Pleural fluid', 'Pleural fluid'),
        ('Saliva', 'Saliva'),
        ('Seminal fluid', 'Seminal fluid'),
        ('Stool', 'Stool'),
        ('Tissue', 'Tissue'),
        ('Urine', 'Urine'),
    )


class DatasetMetadataForm(AbstractEDRNForm):
    '''Form for dataset metadata.'''

    collection = forms.ChoiceField(
        label='LabCAS Collection', help_text='Collection to which the dataset will belong', choices=_collections
    )
    name = forms.CharField(max_length=250, label='Dataset Name', help_text='Enter the name of the dataset')
    description = forms.CharField(help_text='A short summary of this dataset', widget=forms.Textarea)
    investigator = forms.ChoiceField(
        required=False, label='Lead PI', help_text='Select a primary investigator.', choices=pi_choices
    )
    institution = forms.ChoiceField(
        required=False, label='Institution', help_text='Select the curating instutition.', choices=institution_choices
    )
    discipline = forms.MultipleChoiceField(
        required=False, label='Discipline', widget=forms.CheckboxSelectMultiple, choices=discipline_choices
    )
    category = forms.ChoiceField(
        required=False, label='Data Category', help_text='Categorize the data.', choices=data_category_choices
    )
    assay = forms.ChoiceField(
        required=False, label='Assay', widget=forms.RadioSelect, choices=_assays
    )
    content_type = forms.MultipleChoiceField(
        required=False, label='Content Type', help_text='Types of the data in this dataset', choices=_content_types
    )
    specimen_type = forms.MultipleChoiceField(
        required=False, help_text='Select the kinds of specimens collected', choices=_specimen_types
    )
    instrument = forms.CharField(
        required=False, max_length=200, help_text='Name of the scientific instrument used in this dataset'
    )
    processing_software = forms.CharField(
        required=False, max_length=200, help_text='Software programs used to process the dataset'
    )
    private = forms.BooleanField(
        required=False, label='Private Data', help_text='Check this box ↑ if this dataset is private.'
    )
    shared_access = forms.CharField(
        label='Shared Access', required=False, widget=forms.Textarea,
        help_text='If this data is private, enter the names of sites and/or people who should have access, ONE PER LINE.'
    )
    method_details = forms.CharField(required=False, widget=forms.Textarea)
    url_link = forms.URLField(required=False, label='URL Link', help_text='Optional URL link to external or additional data described by this collection.')
    reference_url_description = forms.ChoiceField(
        required=False,
        widget=forms.RadioSelect,
        label='Reference URL Description',
        help_text='Select the description of the resource found at the reference URL.',
        choices=(
            ('cd', 'Clinical Data'),
            ('dbgap', 'dbGAP'),
            ('gdc', 'Genomics Data Commons'),
            ('other', 'Other'),
        )
    )
    reference_url_other = forms.CharField(
        required=False, label='Other', max_length=280,
        help_text='If you selected "Other" above, enter the description of the reference URL.'
    )
    pub_med_id = forms.CharField(required=False, label='PubMed ID', max_length=20)
    doi = forms.CharField(required=False, label='DOI', max_length=150, help_text='Digital Object Identifier')
    doi_url = forms.URLField(required=False, label='DOI URL', help_text='URL form of the DOI')

    if not settings.DEBUG:
        captcha = ReCaptchaField()


class DatasetMetadataFormPage(AbstractFormPage, EmailFormMixin):
    '''Page containing the form for dataset metadata.'''
    page_description = 'Page containing a form for dataset metadata'
    content_panels = AbstractFormPage.content_panels + [
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address', classname='col6', help_text='From whom this email will originate'),
                FieldPanel('to_address', classname='col6', help_text='Who should receive this email; commas in between multiple addresses')
            ]),
            FieldPanel('subject')
        ], 'Email')
    ]
    def get_form(self) -> type:
        return DatasetMetadataForm
    def process_submission(self, form: forms.Form) -> dict:
        if not settings.DEBUG:
            del form.cleaned_data['captcha']
        self.send_mail(form)
        return {'name': form.cleaned_data['name']}
    def get_landing_page(self) -> str:
        return 'edrnsite.content/dataset-metadata-landing.html'
    def _code(self, identifier: str) -> str:
        return urlparse(identifier).path.split('/')[-1]
    def render_email(self, form):
        data = form.cleaned_data
        cp = ConfigParser()
        cp.optionxform = lambda option: option
        cp.add_section('Dataset')
        cp.set('Dataset', 'DatasetName', data['name'])
        cp.set('Dataset', 'DatasetDescription', data['description'])

        if data['investigator']:
            pi = Person.objects.filter(identifier=data['investigator']).first()
            if pi:
                cp.set('Dataset', 'InvestigatorID', self._code(data['investigator']))
                cp.set('Dataset', 'InvestigatorName', pi.title)

        if data['institution']:
            site = Site.objects.filter(identifier=data['institution']).first()
            if site:
                cp.set('Dataset', 'Institution', self._code(data['institution']))
                cp.set('Dataset', 'InstitutionName', site.title)

        if data['discipline']:
            cp.set('Dataset', 'Discipline', '|'.join(data['discipline']))

        if data['content_type']:
            cp.set('Dataset', 'ContentType', '|'.join(data['content_type']))

        if data['specimen_type']:
            cp.set('Dataset', 'SpecimenType', '|'.join(data['specimen_type']))

        if not data['private']: cp.set('Dataset', 'OwnerPrincipal', ALL_USERS_DN)
        if data['shared_access']:
            cp.set(
                'Dataset', 'OwnerPrincipal',
                '|'.join([f'cn={i},dc=edrn,dc=jpl,dc=nasa,dc=gov' for i in data['shared_access'].splitlines()])
            )

        for field, cde in (
            ('category', 'DataCategory'),
            ('assay', 'AssayType'),
            ('instrument', 'Instrument'),
            ('processing_software', 'ProcessingSoftware'),
            ('method_details', 'MethodDetails'),
            ('url_link', 'ReferenceURL'),
            ('reference_url_description', 'ReferenceURLDescription'),
            ('reference_url_other', 'ReferenceURLOther'),
            ('doi', 'DOI'),
            ('doi_url', 'DOIURL')
        ):
            if data[field]:
                cp.set('Dataset', cde, data[field])

        buffer = StringIO()
        cp.write(buffer)
        return buffer.getvalue()
