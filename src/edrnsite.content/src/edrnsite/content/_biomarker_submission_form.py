# encoding: utf-8

'''😌 EDRN Site Content: metadata collection form.'''

from .base_forms import (
    AbstractEDRNForm, pi_site_choices, protocol_choices, organ_choices
)
from .base_models import AbstractFormPage
from captcha.fields import ReCaptchaField
from django import forms
from .tasks import send_email
from django.conf import settings
from eke.knowledge.models import Person, Protocol, BodySystem, Site
from urllib.parse import urlparse
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.contrib.forms.models import EmailFormMixin
from django.core.exceptions import ValidationError


class BiomarkerSubmissionForm(AbstractEDRNForm):
    '''Form to make biomarkers submit.'''

    @staticmethod
    def get_encoding_type() -> str:
        return 'multipart/form-data'

    template_name = 'edrnsite.content/biomarker-submission-form.html'
    _file_help_text = "A file describing new biomarker(s); PDF preferred but Word is acceptable. If you use this option, there's no need to enter any text in the next box." 
    _text_help_text = "Describe the biomarker(s) being submitted. If you use this option, there's no need to upload a file."

    submitter_name = forms.CharField(
        label='Submitter Name', help_text='The name of the person submitting a biomarker.', max_length=100
    )
    submitter_email = forms.EmailField(label='Submitter Email', help_text="Submitter's email address.")

    biomarker_file = forms.FileField(
        label='Biomarker(s) File', help_text=_file_help_text, allow_empty_file=False, required=False
    )
    biomarker_text = forms.CharField(
        label='Biomarker(s) Researched', help_text=_text_help_text, required=False, max_length=5000,
        widget=forms.Textarea
    )
    pi_site = forms.ChoiceField(
        label='Lead PI and Institution',
        help_text='Select a primary investigator and the institution to which they belong.',
        choices=pi_site_choices,
        required=False
    )

    protocol = forms.ChoiceField(
        label='Protocol ID',
        help_text="Select the EDRN protocol/study from which the biomarker was researched. Contact the DMCC if you need to obtain an EDRN protocol.",
        choices=protocol_choices,
        required=False
    )
    organs = forms.MultipleChoiceField(
        label='Organs', help_text='Select the body systems. You can select more than one.', choices=organ_choices,
        required=False
    )
    biomarker_types = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Biomarker Type',
        help_text='Select the kinds of biomarker(s). You can select more than one, but check at least one.',
        choices=(
            ('molecular', 'Molecular'),
            ('histologic', 'Histologic'),
            ('radiographic', 'Radiographic'),
            ('physiological', 'Physiological')
        )
    )
    molecular_subtype = forms.ChoiceField(
        widget=forms.RadioSelect,
        required=False,
        label='Molecular Subtype',
        help_text='If you selected "Molecular" as a type, please indicate the subtype by checking a box here.',
        choices=(
            ('chemical', 'Chemical'),
            ('protein', 'Protein'),
            ('dna', 'DNA (Genetics)'),
            ('karyotypic', 'Karyotypic'),
        )
    )
    associated_publication = forms.CharField(
        required=False,
        max_length=500,
        help_text="Enter the associated publication's PubMed ID or its title."
    )

    if not settings.DEBUG:
        captcha = ReCaptchaField()

    def clean(self):
        cleaned_data = super().clean()

        f, t = cleaned_data.get('biomarker_file'), cleaned_data.get('biomarker_text')
        if not f and not t:
            raise ValidationError('You must either provide a file or fill in the text box describing biomarkers.')
        elif f and t:
            raise ValidationError('Please provide only a file or fill in the text box describing biomarkers—not both.')

        t, st = cleaned_data.get('biomarker_types'), cleaned_data.get('molecular_subtype')
        if t and 'molecular' in t and not st:
            raise ValidationError('If you select "molecular" as a type, you must also select a subtype.')

        return cleaned_data


class BiomarkerSubmissionFormPage(AbstractFormPage, EmailFormMixin):
    '''Page containing a form for making biomarkers submit.'''
    page_description = 'Page containing a form for biomarker submission'

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
        return BiomarkerSubmissionForm

    def get_initial_values(self, request) -> dict:
        initial = super().get_initial_values(request)
        if request.user.is_authenticated:
            try:
                name = request.user.ldap_user.attrs['cn'][0]
            except (AttributeError, KeyError, IndexError, TypeError):
                name = f'{request.user.first_name} {request.user.last_name}'.strip()
            initial['submitter_name'] = name
            try:
                email = request.user.ldap_user.attrs['mail'][0]
            except (AttributeError, KeyError, IndexError, TypeError):
                email = request.user.email
            initial['submitter_email'] = email
        return initial

    def get_landing_page(self) -> str:
        return 'edrnsite.content/biomarker-submission-landing.html'

    def _code(self, identifier: str) -> str:
        return urlparse(identifier).path.split('/')[-1]

    def process_submission(self, form: forms.Form) -> dict:
        # The ``EmailFormMixin`` nicely provides both the from/to/subject fields and also this handy function:
        #     self.send_mail(form)
        # which we can't use since it doesn't handle attachments.
        if not settings.DEBUG:
            del form.cleaned_data['captcha']
        data = form.cleaned_data
        rendered = f'Submitter Name: {data["submitter_name"]}\nSubmitter Email: {data["submitter_email"]}'

        site_id, pi_id = data['pi_site'].split('-')
        pi = Person.objects.filter(personID=pi_id).first()
        if pi:
            rendered += f'\nPI ID: {pi_id}'
            rendered += f'\nPI Name: {pi.title}'
        site = Site.objects.filter(dmccSiteID=site_id).first()
        if site:
            rendered += f'\nInstitution ID: {site_id}'
            rendered += f'\nInstitution Name: {site.title}'

        protocol = Protocol.objects.filter(identifier=data['protocol']).first()
        if protocol:
            rendered += f'\nProtocol ID: {self._code(data["protocol"])}'
            rendered += f'\nProtocol Name: {protocol.title}'

        organ_identifiers = data.get('organs')
        if organ_identifiers:
            names = [i for i in BodySystem.objects.filter(
                identifier__in=organ_identifiers
            ).order_by('title').values_list('title', flat=True)]
            rendered += f'\nOrgans: {", ".join(names)}'

        types = data.get('biomarker_types')
        if types:
            rendered += f'\nBiomarker Types: {", ".join(types)}'

        subtype = data.get('molecular_subtype')
        if subtype:
            rendered += f'\nMolecular Subtype: {subtype}'

        associated_publication = data.get('associated_publication')
        if associated_publication:
            rendered += f'\nAssociated Publication: {associated_publication}'

        biomarker_file = form.cleaned_data['biomarker_file']
        if biomarker_file:
            rendered += '\nA biomarker file was uploaded; it is attached'
            attachment_data = biomarker_file.read()
            send_email(
                self.from_address, self.to_address.split(','), self.subject, rendered,
                {'name': biomarker_file.name, 'data': attachment_data, 'content_type': biomarker_file.content_type}, 10
            )
        else:
            rendered += f'\nBiomarker(s) Researched:\n{data["biomarker_text"]}'
            send_email(self.from_address, self.to_address.split(','), self.subject, rendered, None, 10)

        # And we're done
        return {'name': form.cleaned_data['submitter_name'], 'email': form.cleaned_data['submitter_email']}
