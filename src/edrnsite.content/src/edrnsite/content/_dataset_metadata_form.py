# encoding: utf-8

from .base_forms import AbstractEDRNForm, pi_choices, institution_choices, discipline_choices, data_category_choices
from .base_models import AbstractFormPage
from captcha.fields import ReCaptchaField
from eke.knowledge.models import DataCollection
from django import forms
from django.conf import settings
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.contrib.forms.models import EmailFormMixin
import mimetypes

mimetypes.init()


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
    )


def _content_types():
    return sorted(list(set([(i, i) for i in mimetypes.types_map.values()])))


class DatasetMetadataForm(AbstractEDRNForm):
    '''Form for dataset metadata.'''

    collection = forms.ChoiceField(
        label='LabCAS Collection', help_text='Collection to which the dataset will belong', choices=_collections
    )
    name = forms.CharField(max_length=250, label='Dataset Name', help_text='Enter the name of the dataset')
    description = forms.CharField(help_text='A short summary of this dataset', widget=forms.Textarea)
    investigator = forms.ChoiceField(label='Lead PI', help_text='Select a primary investigator.', choices=pi_choices)
    institution = forms.ChoiceField(label='Institution', help_text='Select the curating instutition.', choices=institution_choices)
    discipline = forms.MultipleChoiceField(label='Discipline', widget=forms.CheckboxSelectMultiple, choices=discipline_choices)
    category = forms.ChoiceField(label='Data Category', help_text='Categorize the data.', choices=data_category_choices)
    assay = forms.ChoiceField(label='Assay', widget=forms.RadioSelect, choices=_assays)
    content_type = forms.MultipleChoiceField(
        label='Content Type', help_text='MIME types of the data in this dataset', choices=_content_types
    )
    specimen_type = forms.CharField(max_length=100, help_text='Enter the kinds of specimens collected')
    instrument = forms.CharField(max_length=200, help_text='Name of the scientific instrument used in this dataset')
    processing_software = forms.CharField(max_length=200, help_text='Software programs used to process the dataset')
    private = forms.BooleanField(required=False, label='Private Data', help_text='Check this box ↑ if this dataset is private.')
    shared_access = forms.CharField(
        label='Shared Access', required=False, widget=forms.Textarea,
        help_text='If this data is private, enter the names of sites and/or people who should have access, ONE PER LINE.'
    )
    method_details = forms.CharField(widget=forms.Textarea)
    url_link = forms.URLField(required=False, label='URL Link', help_text='Optional URL link to external or additional data described by this collection.')
    reference_url_description = forms.ChoiceField(
        required=False,
        widget=forms.RadioSelect,
        label='Reference URL Description',
        help_text='Select the description of the resource found at the reference URL.',
        choices=(
            ('gdc', 'Genomics Data Commons'),
            ('cd', 'Clinical Data'),
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
