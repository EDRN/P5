# encoding: utf-8

'''😌 EDRN Site Content: Django forms.'''


from .base_forms import AbstractEDRNForm
from .base_models import AbstractFormPage
from captcha.fields import ReCaptchaField
from django import forms
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.contrib.forms.models import EmailFormMixin
from wagtail.fields import RichTextField
from django.utils.text import slugify


def _ref_sets():
    choices = (
        'MSA/bladder',
        'Benign Breast Disease',
        'Breast Reference Set and Imaging',
        'Cancers in women—BRSCW',
        'Colon Cancer',
        'DCP/Liver Rapid set',
        'DCP/Liver Validation set',
        'Lung Ref Set A Phase 2 Validation (Retrospective)',
        'Lung Ref Set B (Retrospective)',
        'Pancreatic cancer',
        'Prostate cancer (from PCA3)',
        'Panc Cyst',
    )
    return [(slugify(i), i) for i in choices]


class SpecimenReferenceSetRequestForm(AbstractEDRNForm):
    '''Form to request specimen reference sets.'''

    @staticmethod
    def get_encoding_type() -> str:
        return 'multipart/form-data'

    template_name = 'edrnsite.content/spec-req-form.html'
    _funding_help_text = '''Explain how testing of the reference set(s) will be funded. If there is a current
    NIH-funded grant, enter the grant №, annual direct costs, and funding period. If there is other sponsorship,
    provide a statement of committment from the sponsoring agency, company, or foundation. If there is some
    other funding, please specify.'''
    _proposal_help_text = '''PDF file preferred, but Word is also acceptable; 3–5 pages please.'''
    _sale_help_text = '''By checking this box, I agree not to resell or release the reference set or sub-aliquots
    from this set to an investigator not directly connected with this application.'''
    _complete_help_text = '''By checking this box, I agree to complete the assays on the reference set specimens and return results to the EDRN DMCC within 6 months of their receipt with an opportunity for an extension.'''
    _labcas_help_text = '''By checking this box, I agree to release assay results for posting on LabCAS, a secure domain
    on the EDRN website, 3 months after I have received the unblinded results back from the DMCC for my review.'''

    ref_sets = forms.MultipleChoiceField(
        label='Reference Sets', help_text='Select one or more reference sets', choices=_ref_sets
    )

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
    organ_site = forms.CharField(label='Organ Site(s)', help_text='For example, "lung, ovary".')
    specimen_type = forms.ChoiceField(
        required=True,
        label='Specimen Type',
        help_text='Select the kind of specimen; if you select Other, fill in the next blank.',
        choices=(
            ('buffy coat', 'Buffy Coat'),
            ('cystic fluid', 'Cystic Fluid'),
            ('data-only', 'Data only'),
            ('imaging', 'Imaging'),
            ('plasma', 'Plasma'),
            ('serum', 'Serum'),
            ('stool', 'Stool'),
            ('tissue', 'Tissue'),
            ('urine', 'Urine'),
            ('other', 'Other, specify →'),
        )
    )
    other_specimen_type = forms.CharField(
        required=False, help_text='If you selected "Other", enter the desired specimen type.'
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

    # funding = forms.CharField(label='Funding', help_text=_funding_help_text, widget=forms.Textarea)
    nih_funding = forms.BooleanField(required=False, label='Current NIH-funded grant')
    grant_number = forms.CharField(required=False, label='Grant number', max_length=30)
    annual_direct_costs = forms.CharField(required=False, label='Annual direct costs', max_length=30)
    funding_period = forms.CharField(required=False, label='Funding period', max_length=30)

    other_sponsorship = forms.BooleanField(required=False, label='Other Sponsorship')

    other_funding = forms.BooleanField(required=False, label='Other funding')
    funding_specification = forms.CharField(required=False, label='Specify funding', widget=forms.Textarea)

    proposal = forms.FileField(label='Scientific Proposal', help_text=_proposal_help_text, allow_empty_file=False)

    sale = forms.BooleanField(label='No Sale or Release', help_text=_sale_help_text)
    completion = forms.BooleanField(label='Assay Completion', help_text=_complete_help_text)
    labcas = forms.BooleanField(label='LabCAS Posting', help_text=_labcas_help_text)
    signature = forms.CharField(label='Signature', help_text='Type your name in lieu of providing a signature.', max_length=100)
    captcha = ReCaptchaField()


class SpecimenReferenceSetRequestFormPage(AbstractFormPage, EmailFormMixin):
    '''Page containing a form for specimen reference set requests.'''
    page_description = 'Page containing a form for specimen reference set requests'
    proposal_advice = RichTextField(
        blank=True, help_text='Enter the advice on filling out the "Scientific Proposal" section.'
    )
    content_panels = AbstractFormPage.content_panels + [
        FieldPanel('proposal_advice'),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address', classname='col6', help_text='From whom this email will originate'),
                FieldPanel('to_address', classname='col6', help_text='Who should receive this email; commas in between multiple addresses')
            ]),
            FieldPanel('subject')
        ], 'Email')
    ]

    def get_form(self) -> type:
        return SpecimenReferenceSetRequestForm

    def process_submission(self, form: forms.Form) -> dict:
        self.send_mail(form)
        return {'name': form.cleaned_data['name'], 'email': form.cleaned_data['email']}

    def get_initial_values(self, request) -> dict:
        initial = super().get_initial_values(request)
        if request.user.is_authenticated:
            try:
                name = request.user.ldap_user.attrs['cn'][0]
            except (AttributeError, KeyError, IndexError, TypeError):
                name = f'{request.user.first_name} {request.user.last_name}'.strip()
            initial['name'] = name
        return initial

    def get_landing_page(self) -> str:
        return 'edrnsite.content/spec-req-landing.html'
