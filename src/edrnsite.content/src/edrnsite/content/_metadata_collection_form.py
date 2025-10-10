# encoding: utf-8

'''😌 EDRN Site Content: metadata collection form.'''

from .base_forms import (
    AbstractEDRNForm, pi_site_choices, discipline_choices, data_category_choices, ALL_USERS_DN,
    protocol_choices, organ_choices
)
from .base_models import AbstractFormPage
from django_recaptcha.fields import ReCaptchaField
from configparser import ConfigParser
from django import forms
from django.conf import settings
from eke.knowledge.models import Person, Protocol, BodySystem, Site
from io import StringIO
from urllib.parse import urlparse
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.contrib.forms.models import EmailFormMixin
import datetime


def _collab_groups():
    '''Return a vocabulary of collaborative groups.

    Normally we'd want to use CollaborativeGroupSnippet but there's a nasty
    circular dependency that prevents it from being used here. This form should
    be in its own module and not in edrnsite.content, which would fix that.

    Also, LabCAS drops the "Cancers Research Group" from each collab group name.
    '''
    return [
        ('breast', 'Breast and Gynecologic'),
        ('gi', 'G.I. and Other Associated'),
        ('lung', 'Lung and Upper Aerodigestive'),
        ('prostate', 'Prostate and Urologic')
    ]


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

    _desc_help = '''Provide a short description of the data in this collection. Explain the methods and
procedures used to collect the data, including any equipment, software, or protocols utilized. Additionally,
detail any processing or transformation steps applied to the data at the collection sites, such as
normalization, filtering, or algorithmic processing.'''
    _method_details_help = '''A comprehensive description of the methodologies and procedures used in the
collection and processing of the dataset. This includes information on the experimental design, data collection
techniques, equipment used, protocols followed, and any specific conditions or settings applied during the data
acquisition process. Additionally, it captures details about any tools, software, or algorithms utilized in
data processing and analysis, ensuring transparency and reproducibility of the research.'''
    _instrument_help = '''The specific device or apparatus used to generate the data. This can include mass
spectrometers, sequencers, imaging devices (e.g., MRI, CT, Mammogram), and other specialized tools employed
in the data collection process.'''

    collection_name = forms.CharField(label='Collection Name', help_text='The name or title of your data collection.')
    description = forms.CharField(label='Collection Description', help_text=_desc_help, widget=forms.Textarea)
    custodian = forms.CharField(label='Data Custodian', help_text='The name of the person that will be contacted with questions about this data collection.')
    custodian_email = forms.EmailField(label='Data Custodian Email', help_text='The email of the person that will be contacted with questions about this data collection.')
    pi_site = forms.ChoiceField(label='Lead PI and Institution', help_text='Select a primary investigator and the institution to which they belong.', choices=pi_site_choices)
    additional_site = forms.CharField(
        label='Additional Researcher and Institution',
        help_text='Additional researchers, separated by commas, in priority order.',
        required=False, max_length=512
    )
    protocol = forms.ChoiceField(label='Protocol', help_text='Select the protocol that generated the data.', choices=protocol_choices)
    biomarkers_researched = forms.CharField(
        required=False, label='Biomarkers Researched', widget=forms.Textarea, max_length=5000,
        help_text='Enter the name(s) of the cancer biomarker(s) associated with the data being deposited.'
    )
    cg = forms.ChoiceField(
        label='Collaborative Group', help_text='Select the collaborative research group',
        widget=forms.RadioSelect,
        choices=_collab_groups()
    )
    discipline = forms.MultipleChoiceField(label='Discipline', widget=forms.CheckboxSelectMultiple, choices=discipline_choices)
    other_discipline = forms.CharField(
        required=False, label='Other Discipline', max_length=60,
        help_text='If choosing "Other" above ↑, please enter the name of the discipline.'
    )
    method_details = forms.CharField(label='Method Details', help_text=_method_details_help, widget=forms.Textarea)
    instrument = forms.CharField(label='Instrument', help_text=_instrument_help, max_length=100)
    category = forms.ChoiceField(label='Data Category', help_text='Categorize the data.', choices=data_category_choices)
    other_category = forms.CharField(
        label='Other Data Category', help_text='If you selected Other above ↑, enter the category here.',
        max_length=100, required=False
    )
    organ = forms.ChoiceField(label='Organ', help_text='Select the body system.', choices=organ_choices)
    species = forms.ChoiceField(label='Species', help_text='Enter the species.', choices=_species)
    results = forms.CharField(
        required=True, label='Results and Conclusion Summary', widget=forms.Textarea,
        help_text='The results and conclusions from this data collection.'
    )

    # EDRN/P5#403 — HK wants to hold off
    # data_structure_description = forms.CharField(
    #     required=True, label='Data Structure Description', widget=forms.Textarea,
    #     help_text='Describe the structure of the data.'
    # )
    # data_capture_start_date = forms.DateField(
    #     required=True, widget=forms.DateInput(attrs={'type': 'date'}), initial=datetime.date.today
    # )
    # data_capture_end_date = forms.DateField(
    #     required=True, widget=forms.DateInput(attrs={'type': 'date'}), initial=datetime.date.today
    # )
    reference_url_description = forms.ChoiceField(
        required=False,
        widget=forms.RadioSelect,
        label='URL Description',
        help_text='Select the description of the reference URL used to reference additional information or point to data in external repositories. The URL is entered below.',
        choices=(
            ('cd', 'Clinical Data'),
            ('dbgap', 'dbGAP'),
            ('gdc', 'Genomics Data Commons'),
            ('other', 'Other'),
        )
    )
    reference_url_other = forms.CharField(
        required=False, label='Other', max_length=280,
        help_text='If you selected "Other" above, enter the description of the URL.'
    )
    reference_url = forms.URLField(required=False, label='URL Link', help_text='URL link to external or additional data described by this collection.')
    pub_med_id = forms.CharField(required=False, label='PubMed ID', max_length=20)
    doi = forms.CharField(required=False, label='DOI', max_length=150, help_text='Digital Object Identifier that is associated with the data being described.')
    doi_url = forms.URLField(required=False, label='DOI URL', help_text='URL form of the DOI that is associated with the data being described.')
    access_groups = forms.CharField(
        label='Shared Access', required=False, widget=forms.Textarea,
        help_text='If this data is private, enter the names of sites and/or people who should have access, ONE PER LINE.'
    )
    private = forms.BooleanField(required=False, label='Private Data', help_text='Check this box ↑ if this data collection is private.')
    comments = forms.CharField(
        required=False, label='Comments or Questions', widget=forms.Textarea, max_length=5000,
        help_text='Have questions? Need to clarify something? Want to make some comments? Enter here.'
    )
    type_of_data = forms.CharField(
        required=False, max_length=512, label='Type of data files to be uploaded',
        help_text='Describe the type of data files that are to be uploaded.'
    )
    if not settings.DEBUG:
        captcha = ReCaptchaField()


class MetadataCollectionFormPage(AbstractFormPage, EmailFormMixin):
    '''Page containing a form for metadata collection.'''
    page_description = 'Page containing a form for metadata collection'

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
        cp = ConfigParser(interpolation=None)
        cp.optionxform = lambda option: option
        cp.add_section('Collection')
        cp.set('Collection', 'CollectionName', data['collection_name'])
        cp.set('Collection', 'CollectionDescription', data['description'])

        site_id, pi_id = data['pi_site'].split('-')

        pi = Person.objects.filter(personID=pi_id).first()
        cp.set('Collection', 'LeadPIId', pi_id)
        cp.set('Collection', 'LeadPI', pi.title)

        cp.set('Collection', 'DataCustodian', data['custodian'])
        cp.set('Collection', 'DataCustodianEmail', data['custodian_email'])

        site = Site.objects.filter(dmccSiteID=site_id).first()
        cp.set('Collection', 'InstitutionId', site_id)
        cp.set('Collection', 'Institution', site.title)

        protocol = Protocol.objects.filter(identifier=data['protocol']).first()
        cp.set('Collection', 'ProtocolId', self._code(data['protocol']))
        cp.set('Collection', 'ProtocolName', protocol.title)
        cp.set('Collection', 'ProtocolAbbreviatedName', protocol.abbreviation)

        if data['discipline']:
            disc_names = {i[0]: i[1] for i in discipline_choices()}
            discs = [disc_names[i] for i in data['discipline']]
            cp.set('Collection', 'Discipline', '|'.join(discs))
        cp.set(
            'Collection', 'DataCategory',
            {i[0]: i[1] for i in data_category_choices()}[data['category']]
        )

        bs = BodySystem.objects.filter(identifier=data['organ']).first()
        cp.set('Collection', 'OrganId', self._code(data['organ']))
        cp.set('Collection', 'Organ', bs.title)

        cp.set(
            'Collection', 'CollaborativeGroup',
            {i[0]: i[1] for i in _collab_groups()}[data['cg']]
        )

        if data['results']: cp.set('Collection', 'ResultsAndConclusionSummary', data['results'])
        if data['pub_med_id']: cp.set('Collection', 'PubMedID', data['pub_med_id'])
        if data['reference_url']: cp.set('Collection', 'ReferenceURLLink', data['reference_url'])

        if data['reference_url_description']:
            cp.set('Collection', 'ReferenceURLDescription', data['reference_url_description'])
        if data['reference_url_other']: cp.set('Collection', 'ReferenceURLOther', data['reference_url_other'])
        cp.set('Collection', 'Consortium', 'EDRN')
        cp.set(
            'Collection', 'Species',
            {i[0]: i[1] for i in _species()}[data['species']]
        )

        if not data['private']: cp.set('Collection', 'OwnerPrincipal', ALL_USERS_DN)
        if data['access_groups']:
            cp.set(
                'Collection', 'OwnerPrincipal',
                '|'.join([f'cn={i},dc=edrn,dc=jpl,dc=nasa,dc=gov' for i in data['access_groups'].splitlines()])
            )

        if data['doi']: cp.set('Collection', 'DOI', data['doi'])
        if data['doi_url']: cp.set('Collection', 'DOIURL', data['doi_url'])

        # Always add the data disclaimer #372
        from .models import BoilerplateSnippet
        disclaimer = BoilerplateSnippet.objects.filter(bp_code='data-disclaimer').first()
        if not disclaimer:
            disclaimer_text = '«No data disclaimer snippet found in portal snippets»'
        else:
            disclaimer_text = disclaimer.text
        cp.set('Collection', 'DataDisclaimer', disclaimer_text)

        # EDRN/P5#403 — HK wants to hold off
        # cp.set('Collection', 'DataCaptureStartDate', data['data_capture_start_date'].isoformat())
        # cp.set('Collection', 'DataCaptureEndDate', data['data_capture_end_date'].isoformat())

        if data['instrument']: cp.set('Collection', 'Instrument', data['instrument'])
        if data['method_details']: cp.set('Collection', 'MethodDetails', data['method_details'])

        buffer = StringIO()
        cp.write(buffer)

        if data['comments']:
            buffer.write('\n\n\n')
            buffer.write('-' * 40)
            buffer.write('\n\nThe following was entered into the comments section:\n\n')
            buffer.write(data['comments'])

        if data['biomarkers_researched']:
            buffer.write('\n\n\n')
            buffer.write('-' * 40)
            buffer.write('\n\nThe following was entered into the "biomarkers researched" section:\n\n')
            buffer.write(data['biomarkers_researched'])

        if data['additional_site']:
            buffer.write('\n\n\n')
            buffer.write('-' * 40)
            buffer.write('\n\nThe following was entered into the "addtional researcher and institution" field:\n\n')
            buffer.write(data['additional_site'])

        if data['type_of_data']:
            buffer.write('\n\n\n')
            buffer.write('-' * 40)
            buffer.write('\n\nThe following was entered into the "type of data" field:\n\n')
            buffer.write(data['type_of_data'])

        if data['other_discipline']:
            buffer.write('\n\n\n')
            buffer.write('-' * 40)
            buffer.write('\n\nThe following was entered into the "other discipline" field:\n\n')
            buffer.write(data['other_discipline'])

        # EDRN/P5#403 — HK wants to hold off
        # if data['data_structure_description']:
        #     buffer.write('\n\n\n')
        #     buffer.write('-' * 40)
        #     buffer.write('\n\nThe following was entered into the "data structure description" field:\n\n')
        #     buffer.write(data['data_structure_description'])

        return buffer.getvalue()
