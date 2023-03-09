# encoding: utf-8

'''😌 EDRN Site Content: Django forms.'''

from .base_forms import AbstractEDRNForm
from django import forms
from eke.knowledge.models import Site, Person, Protocol, BodySystem


def _pis():
    return [
        (i.identifier, i.title)
        for i in Person.objects.filter(pk__in=Site.objects.values_list('pi', flat=True)).order_by('title')
    ]


def _instutions():
    return [(i.identifier, f'{i.title} ({i.dmccSiteID})') for i in Site.objects.all().order_by('title')]


def _protocols():
    return [(i.identifier, f'{i.title} ({i.protocolID})') for i in Protocol.objects.all().order_by('title')]


def _organs():
    return [(i.identifier, i.title) for i in BodySystem.objects.all().order_by('title')]


def _data_categories():
    categories = (
        'Antibody Microarray',
        'Biospecimen',
        'Clinical',
        'CT',
        'DNA Methylation Sequencing',
        'DNA Microarray Analysis',
        'Documentation',
        'ELISA',
        'Fluoroscopy',
        'Immunoassay',
        'Immunohistochemestry',
        'LabMAP',
        'Luminex',
        'Mammography',
        'Mass Spectrometry',
        'MRI',
        'Multiplex-Immunofluorescent Staining',
        'PET',
        'Protein Microarray',
        'Radiomics',
        'RNA Sequencing',
        'Sequencing',
        'Single Slide Image',
        'Tissue Micro Array',
        'Whole Slide Imaging',
    )
    return [(i.lower().replace(' ', '-'), i) for i in categories]


def _species():
    species = (
        'Homo sapiens',
        'Mus musculus',
        'Bos taurus',
        'Escherichia coli',
        'Rattus norvegicus',
        'Caenorhabditis elegans',
        'Cricetulus griseus',
        'Saccharomyces cerevisiae',
    )
    return [(i.lower().replace(' ', '-'), i) for i in species]


class MetadataCollectionForm(AbstractEDRNForm):
    '''Form to collect metadata.'''

    collection_name = forms.CharField(label='Collection Name', help_text='Name of this collection.')
    description = forms.CharField(label='Collection Description', help_text='A short summary of this collection.', widget=forms.Textarea)
    custodian = forms.CharField(label='Data Custodian', help_text='Genrally, this is your name.')
    custodian_email = forms.EmailField(label='Data Custodian Email', help_text='Email address for the data custodian.')
    lead_pi = forms.ChoiceField(label='Lead PI', help_text='Select a primary investigator.', choices=_pis)
    institution = forms.ChoiceField(label='Institution', help_text='Select the curating instutition.', choices=_instutions)
    protocol = forms.ChoiceField(label='Protocol', help_text='Select the protocol that generated the data.', choices=_protocols)
    discipline = forms.ChoiceField(label='Discipline', widget=forms.RadioSelect, choices=(
        ('genomics', 'Genomics'),
        ('proteomics', 'Proteomics'),
        ('pathology-images', 'Pathology Imagess'),
        ('radiology', 'Radiology'),
        ('immunology', 'Immunology'),
        ('pathology', 'Pathology'),
        ('undefined', 'Undefined')
    ))
    cg = forms.ChoiceField(
        label='Collaborative Group', help_text='Select the collaborative research group',
        widget=forms.RadioSelect,
        choices=(
            ('breast-gyn', 'Breast & Gynecological Cancers Research Group'),
            ('colorect-gi', 'Colorectal & Other GI Cancers Research Group'),
            ('lung', 'Lung & Upper Aerodigestive Cancers Research Group'),
            ('prostate', 'Prostate & Other Urologic Cancers Research Group'),
        )
    )
    category = forms.ChoiceField(label='Data Category', help_text='Categorize the data.', choices=_data_categories)
    organ = forms.ChoiceField(label='Organ', help_text='Select the body system.', choices=_organs)
    species = forms.ChoiceField(label='Species', help_text='Enter the species.', choices=_species)
    private = forms.BooleanField(required=False, label='Private Data', help_text='Check this box ↑ if this data collection is private.')
    access_groups = forms.CharField(
        label='Shared Access', required=False, widget=forms.Textarea,
        help_text='If this data is private, enter the names of sites and/or people who should have access, ONE PER LINE.'
    )
    method = forms.CharField(required=False, label='Method Details', widget=forms.Textarea)  # is this needed?
    results = forms.CharField(required=False, label='Results and Conclusion Summary', widget=forms.Textarea)
    reference_url = forms.URLField(required=False, label='Reference URL', help_text='Optional URL to reference with this collection.')
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
    pub_med_id = forms.CharField(required=False, label='PubMed ID', max_length=20)
    doi = forms.CharField(required=False, label='DOI', max_length=150, help_text='Digital Object Identifier')
    doi_url = forms.URLField(required=False, label='DOI URL', help_text='URL form of the DOI')
