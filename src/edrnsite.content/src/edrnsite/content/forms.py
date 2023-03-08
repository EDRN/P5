# encoding: utf-8

'''😌 EDRN Site Content: Django forms.'''

from captcha.fields import ReCaptchaField
from django import forms
from django.forms.utils import ErrorList
from eke.knowledge.models import Site, Person, Protocol, BodySystem


class EDRNErrorList(ErrorList):
    def __init__(self, initlist=None, error_class=None, renderer=None):
        if error_class is None:
            error_class = 'text-danger'
        super().__init__(initlist, error_class, renderer)


class AbstractEDRNForm(forms.Form):
    '''This is an abstract form that sets up our preferred styles.'''
    template_name = 'edrnsite.content/form-rendering.html'
    template_name_label = 'edrnsite.content/label-rendering.html'
    error_css_class = 'is-invalid'
    required_css_class = 'is-required'

    def __init__(
        self,
        data=None,
        files=None,
        auto_id='id_%s',
        prefix=None,
        initial=None,
        error_class=EDRNErrorList,
        label_suffix=None,
        empty_permitted=False,
        field_order=None,
        use_required_attribute=None,
        renderer=None,
        page=None
    ):
        super().__init__(
            data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, field_order,
            use_required_attribute, renderer
        )
        self.page = page

    class Meta:
        abstract = True


class SpecimenReferenceSetRequestForm(AbstractEDRNForm):
    '''Form to request specimen reference sets.'''

    template_name = 'edrnsite.content/spec-req-form.html'

    _funding_help_text = '''Explain how testing of the reference set(s) will be funded. If there is a current
    NIH-funded grant, enter the grant №, annual direct costs, and funding period. If there is other sponsorship,
    provide a statement of committment from the sponsoring agency, company, or foundation. If there is some
    other funding, please specify.'''
    _proposal_help_text = '''Enter about 3–5 pages worth of text as recommended in the preamble to this form.'''
    _sale_help_text = '''By checking this box, I agree not to resell or release the reference set or sub-aliquots
    from this set to an investigator not directly connected with this application.'''
    _complete_help_text = '''By checking this box, I agree to complete the assays on the reference set specimens and
    return results to the EDRN DMCC within 4 months of their receipt.'''
    _labcas_help_text = '''By checking this box, I agree to release assay results for posting on LabCAS, a secure domain
    on the EDRN website, 3 months after I have received the unblinded results back from the DMCC for my review.'''

    investigator = forms.CharField(label='Investigator', help_text='Name of the investigator.', max_length=100)
    name = forms.CharField(label='Your Name', help_text='The name of the person filling out this form.', max_length=100)
    institution = forms.CharField(label='Institution', help_text='Institution requesting the specimens.', max_length=250)
    email = forms.EmailField(label='Email', help_text='Email address at which you can be reached.')
    phone = forms.CharField(label='Phone', help_text='Contact telephone number.', max_length=25, required=False)
    collaborative_group_oversight = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Collaborative Group Oversight',
        help_text='Select all that apply.',
        choices=(
            ('breast-gyn', 'Breast & Gynecological'),
            ('colorect-gi', 'Colorectal & Other GI'),
            ('lung', 'Lung & Upper Aerodigestive'),
            ('prostate', 'Prostate & Other Urologic'),
        )
    )
    organ_site = forms.CharField(label='Organ Site(s)', help_text='For example, "lung, ovary").')
    specimen_type = forms.ChoiceField(
        required=True,
        widget=forms.RadioSelect,
        label='Specimen Type',
        help_text='Select the kind of specimen; if you select Other, fill in the next blank.',
        choices=(
            ('serum', 'Serum'),
            ('plasma', 'Plasma'),
            ('other', 'Other'),
        )
    )
    other_specimen_type = forms.CharField(
        required=False, help_text='If you selected "Other" previously, enter the desired specimen type.'
    )
    min_volume = forms.DecimalField(
        label='Minimum Volume', min_value=0,
        help_text='The minimum volume of each sample requested in μL (microliters).'
    )
    study_length = forms.IntegerField(label='Study Length', help_text='Expected duration of the study in months.', min_value=0)
    irb_approval = forms.ChoiceField(
        label='IRB Approval', widget=forms.RadioSelect,
        help_text='Do you have approval from your Institutional Review Board to work with the requested samples?',
        choices=(('yes', 'Yes'), ('no', 'No'), ('pending', 'Pending'))
    )
    irb_explanation = forms.CharField(
        label='IRB Elaboration', required=False,
        help_text='If you answered "yes", enter your IRB number. If you answered "pending", enter the expected approval date.'
    )
    funding = forms.CharField(label='Funding', help_text=_funding_help_text, widget=forms.Textarea)
    proposal = forms.CharField(label='Scientific Proposal', help_text=_proposal_help_text, widget=forms.Textarea)
    sale = forms.BooleanField(label='No Sale or Release', help_text=_sale_help_text)
    completion = forms.BooleanField(label='Assay Completion', help_text=_complete_help_text)
    labcas = forms.BooleanField(label='LabCAS Posting', help_text=_labcas_help_text)
    signature = forms.CharField(label='Signature', help_text='Type your name in lieu of providing a signature.', max_length=100)
    captcha = ReCaptchaField()


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


class MetadataCollectionForm(AbstractEDRNForm):
    '''Form to collect metadata.'''

    collection_name = forms.CharField(label='Collection Name', help_text='Name of this collection.')
    description = forms.CharField(label='Collection Description', help_text='A short summary of this collection.', widget=forms.Textarea)
    custodian = forms.CharField(label='Data Custodian', help_text='Genrally, this is your name.')
    custodian_email = forms.EmailField(label='Data Custodian Email', help_text='Email address for the data custodian.')
    lead_pi = forms.ChoiceField(label='Lead PI', help_text='Select a primary investigator.', choices=_pis)
    institution = forms.ChoiceField(label='Institution', help_text='Select the curating instutition.', choices=_instutions)
    protocol = forms.ChoiceField(label='Protocol', help_text='Select the protocol that generated the data.', choices=_protocols)
    discipline = forms.CharField(label='Discipline', max_length=100)
    cg = forms.ChoiceField(
        label='Collaborative Group', help_text='Select the collaborative research group',
        choices=(
            ('breast-gyn', 'Breast & Gynecological Cancers Research Group'),
            ('colorect-gi', 'Colorectal & Other GI Cancers Research Group'),
            ('lung', 'Lung & Upper Aerodigestive Cancers Research Group'),
            ('prostate', 'Prostate & Other Urologic Cancers Research Group'),
        )
    )
    category = forms.CharField(label='Data Category', help_text='Categorize the data.')
    organ = forms.ChoiceField(label='Organ', help_text='Select the body system.', choices=_organs)
    species = forms.CharField(label='Species', help_text='Enter the species.', max_length=100)
    private = forms.BooleanField(required=False, label='Private Data', help_text='Check this box ↑ if this data collection is private.')
    access_groups = forms.CharField(
        label='Shared Access', required=False, widget=forms.Textarea,
        help_text='If this data is private, enter the names of sites and/or people who should have access.'
    )
    method = forms.CharField(required=False, label='Method Details', widget=forms.Textarea)
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
