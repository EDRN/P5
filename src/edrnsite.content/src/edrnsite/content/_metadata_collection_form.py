# encoding: utf-8

'''😌 EDRN Site Content: Django forms.'''

from .base_forms import AbstractEDRNForm
from .base_models import AbstractFormPage
from captcha.fields import ReCaptchaField
from configparser import ConfigParser
from django import forms
from django.conf import settings
from eke.knowledge.models import Site, Person, Protocol, BodySystem
from io import StringIO
from urllib.parse import urlparse
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.contrib.forms.models import EmailFormMixin


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
        'Other (specify below)',
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
    discipline = forms.MultipleChoiceField(label='Discipline', widget=forms.CheckboxSelectMultiple, choices=(
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
    other_category = forms.CharField(
        label='Other Data Category', help_text='If you selected Other above ↑, enter the category here.',
        max_length=100, required=False
    )
    organ = forms.ChoiceField(label='Organ', help_text='Select the body system.', choices=_organs)
    species = forms.ChoiceField(label='Species', help_text='Enter the species.', choices=_species)
    private = forms.BooleanField(required=False, label='Private Data', help_text='Check this box ↑ if this data collection is private.')
    access_groups = forms.CharField(
        label='Shared Access', required=False, widget=forms.Textarea,
        help_text='If this data is private, enter the names of sites and/or people who should have access, ONE PER LINE.'
    )
    results = forms.CharField(required=False, label='Results and Conclusion Summary', widget=forms.Textarea)
    reference_url = forms.URLField(required=False, label='URL Link', help_text='Optional URL link to external or additional data described by this collection.')
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
    comments = forms.CharField(
        required=False, label='Comments or Questions', widget=forms.Textarea, max_length=5000,
        help_text='Have questions? Need to clarify something? Want to make some comments? Enter here.'
    )
    if not settings.DEBUG:
        captcha = ReCaptchaField()


class MetadataCollectionFormPage(AbstractFormPage, EmailFormMixin):
    '''Page containing a form for metadata collection.'''
    page_description = 'Page containing a form for metadata collection'
    _all_users_dn = 'cn=All Users,dc=edrn,dc=jpl,dc=nasa,dc=gov'

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
        return MetadataCollectionForm
    def process_submission(self, form: forms.Form) -> dict:
        if not settings.DEBUG:
            del form.cleaned_data['captcha']
        self.send_mail(form)
        return {'name': form.cleaned_data['custodian'], 'email': form.cleaned_data['custodian_email']}
    def get_initial_values(self, request) -> dict:
        initial = super().get_initial_values(request)
        if request.user.is_authenticated:
            try:
                name = request.user.ldap_user.attrs['cn'][0]
            except (AttributeError, KeyError, IndexError, TypeError):
                name = f'{request.user.first_name} {request.user.last_name}'.strip()
            initial['custodian'] = name
            try:
                email = request.user.ldap_user.attrs['mail'][0]
            except (AttributeError, KeyError, IndexError, TypeError):
                email = request.user.email
            initial['custodian_email'] = email
        return initial
    def get_landing_page(self) -> str:
        return 'edrnsite.content/meta-req-landing.html'
    def _code(self, identifier: str) -> str:
        return urlparse(identifier).path.split('/')[-1]
    def render_email(self, form):
        data = form.cleaned_data
        cp = ConfigParser()
        cp.optionxform = lambda option: option
        cp.add_section('Collection')
        cp.set('Collection', 'CollectionName', data['collection_name'])
        cp.set('Collection', 'CollectionDescription', data['description'])

        pi = Person.objects.filter(identifier=data['lead_pi']).first()
        cp.set('Collection', 'LeadPIID', self._code(data['lead_pi']))
        cp.set('Collection', 'LeadPIName', pi.title)

        cp.set('Collection', 'DataCustodian', data['custodian'])
        cp.set('Collection', 'DataCustodianEmail', data['custodian_email'])

        site = Site.objects.filter(identifier=data['institution']).first()
        cp.set('Collection', 'InstitutionID', self._code(data['institution']))
        cp.set('Collection', 'InstitutionName', site.title)

        protocol = Protocol.objects.filter(identifier=data['protocol']).first()
        cp.set('Collection', 'ProtocolID', self._code(data['protocol']))
        cp.set('Collection', 'ProtocolName', protocol.title)
        cp.set('Collection', 'ProtocolAbbreviatedName', protocol.abbreviation)

        if data['discipline']:
            cp.set('Collection', 'Discipline', '|'.join(data['discipline']))
        cp.set('Collection', 'DataCategory', data['category'])

        bs = BodySystem.objects.filter(identifier=data['organ']).first()
        cp.set('Collection', 'OrganID', self._code(data['organ']))
        cp.set('Collection', 'OrganName', bs.title)

        cp.set('Collection', 'CollaborativeGroup', data['cg'])
        if data['results']: cp.set('Collection', 'ResultsAndConclusionSummary', data['results'])
        if data['pub_med_id']: cp.set('Collection', 'PubMedID', data['pub_med_id'])
        if data['reference_url']: cp.set('Collection', 'ReferenceURL', data['reference_url'])
        if data['reference_url_description']:
            cp.set('Collection', 'ReferenceURLDescription', data['reference_url_description'])
        if data['reference_url_other']: cp.set('Collection', 'ReferenceURLOther', data['reference_url_other'])
        cp.set('Collection', 'Consortium', 'EDRN')
        cp.set('Collection', 'Species', data['species'])

        if not data['private']: cp.set('Collection', 'OwnerPrincipal', self._all_users_dn)
        if data['access_groups']:
            cp.set(
                'Collection', 'OwnerPrincipal',
                '|'.join([f'cn={i},dc=edrn,dc=jpl,dc=nasa,dc=gov' for i in data['access_groups'].splitlines()])
            )

        if data['doi']: cp.set('Collection', 'DOI', data['doi'])
        if data['doi_url']: cp.set('Collection', 'DOIURL', data['doi_url'])

        buffer = StringIO()
        cp.write(buffer)
        if data['comments']:
            buffer.write('\n\n\n')
            buffer.write('-' * 40)
            buffer.write('\n\nThe following was entered into the comments section:\n\n')
            buffer.write(data['comments'])
        return buffer.getvalue()
