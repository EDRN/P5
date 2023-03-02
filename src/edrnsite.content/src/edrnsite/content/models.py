# encoding: utf-8

'''😌 EDRN site content's models.'''


from configparser import ConfigParser
from django import forms
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from edrnsite.streams import blocks
from eke.knowledge.models import Site, Person, Protocol, BodySystem
from io import StringIO
from modelcluster.fields import ParentalKey
from urllib.parse import urlparse
from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField, EmailFormMixin
from wagtail.core import blocks as wagtail_core_blocks
from wagtail.fields import RichTextField
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet
from wagtailcaptcha.models import WagtailCaptchaEmailForm
from wagtailmetadata.models import MetadataPageMixin


class AbstractFormPage(Page):
    '''Abstract base class for Wagtai pages holding Django forms.'''
    intro = RichTextField(blank=True, help_text='Introductory text to appear above the form')
    outro = RichTextField(blank=True, help_text='Text to appear below the form')
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('outro')
    ]

    def get_form(self) -> type:
        '''Return the class of the form this page will display.'''
        raise NotImplementedError('Subclasses must implement get_form')

    def get_initial_values(self, request: HttpRequest) -> dict:
        '''Return any initial values for the form. By default this is an empty dict.
        Subclasses may override this.'''
        return dict()

    def process_submission(self, form: forms.Form) -> dict:
        '''Process the submitted and cleaned ``form``.

        Return a dict of any other parameters that may be needed in the thank you page.
        '''
        raise NotImplementedError('Subclasses must implement process_submission')

    def get_landing_page(self) -> str:
        '''Get the name of the landing (thank you) page for successful submission.'''
        raise NotImplementedError('Subclasses must implement get_landing_page')

    def _bootstrap(self, form: forms.Form):
        '''Add Boostrap class to every widget except checkboxes & radio buttons.'''
        for field in form.fields.values():
            if not isinstance(
                field.widget, (
                    forms.widgets.CheckboxInput, forms.widgets.CheckboxSelectMultiple, forms.widgets.RadioSelect
                )
            ):
                field.widget.attrs.update({'class': 'form-control'})

    def serve(self, request: HttpRequest) -> HttpResponse:
        form_class = self.get_form()
        if request.method == 'POST':
            form = form_class(request.POST)
            if form.is_valid():
                params = {'page': self, **self.process_submission(form)}
                return render(request, self.get_landing_page(), params)
        else:
            form = form_class(initial=self.get_initial_values(request))
        self._bootstrap(form)
        return render(request, 'edrnsite.content/form.html', {'page': self, 'form': form})

    class Meta:
        abstract = True


class SpecimenReferenceSetRequestFormPage(AbstractFormPage, EmailFormMixin):
    '''Page containing a form for specimen reference set requests.'''
    page_description = 'Page containing a form for specimen reference set requests'

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
        from .forms import SpecimenReferenceSetRequestForm
        return SpecimenReferenceSetRequestForm

    def process_submission(self, form: forms.Form) -> dict:
        self.send_mail(form)
        return {'name': form.cleaned_data['name'], 'email': form.cleaned_data['email']}

    def get_initial_values(self, request) -> dict:
        initial = super().get_initial_values(request)
        if request.user.is_authenticated:
            try:
                name = request.user.ldap_user.attrs['cn'][0]
            except (AttributeError, KeyError, IndexError):
                name = f'{request.user.first_name} {request.user.last_name}'.strip()
            initial['name'] = name
        return initial

    def get_landing_page(self) -> str:
        return 'edrnsite.content/spec-req-landing.html'


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
        from .forms import MetadataCollectionForm
        return MetadataCollectionForm
    def process_submission(self, form: forms.Form) -> dict:
        self.send_mail(form)
        return {'name': form.cleaned_data['custodian'], 'email': form.cleaned_data['custodian_email']}
    def get_initial_values(self, request) -> dict:
        initial = super().get_initial_values(request)
        if request.user.is_authenticated:
            try:
                name = request.user.ldap_user.attrs['cn'][0]
            except (AttributeError, KeyError, IndexError):
                name = f'{request.user.first_name} {request.user.last_name}'.strip()
            initial['custodian'] = name
            try:
                email = request.user.ldap_user.attrs['mail'][0]
            except (AttributeError, KeyError, IndexError):
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
        cp.set('Collection', 'Discipline', data['discipline'])
        cp.set('Collection', 'DataCategory', data['category'])
        site = Site.objects.filter(identifier=data['institution']).first()
        cp.set('Collection', 'Institution', site.title)
        cp.set('Collection', 'InstitutionId', self._code(data['institution']))
        pi = Person.objects.filter(identifier=data['lead_pi']).first()
        cp.set('Collection', 'LeadPI', pi.title)
        cp.set('Collection', 'LeadPIId', self._code(data['lead_pi']))
        cp.set('Collection', 'DataCustodian', data['custodian'])
        cp.set('Collection', 'DataCustodianEmail', data['custodian_email'])
        bs = BodySystem.objects.filter(identifier=data['organ']).first()
        cp.set('Collection', 'Organ', bs.title)
        cp.set('Collection', 'OrganId', self._code(data['organ']))
        if not data['private']: cp.set('Collection', 'OwnerPrincipal', self._all_users_dn)
        cp.set('Collection', 'CollaborativeGroup', data['cg'])
        cp.set('Collection', 'Consortium', 'EDRN')
        protocol = Protocol.objects.filter(identifier=data['protocol']).first()
        cp.set('Collection', 'ProtocolName', protocol.title)
        cp.set('Collection', 'ProtocolId', self._code(data['protocol']))
        cp.set('Collection', 'Species', data['species'])
        if data['method']: cp.set('Collection', 'MethodDetails', data['method'])
        if data['results']: cp.set('Collection', 'ResultsAndConclusionSummary', data['results'])
        if data['pub_med_id']: cp.set('Collection', 'PubMedID', data['pub_med_id'])
        if data['access_groups']:
            cp.set('Collection', 'OwnerPrincipal', '|'.join([f'cn={i},dc=edrn,dc=jpl,dc=nasa,dc=gov' for i in data['access_groups'].splitlines()]))
        buffer = StringIO()
        cp.write(buffer)
        return buffer.getvalue()


class HomePage(MetadataPageMixin, Page):
    '''Special content type for the home page of the entire site.'''
    template = 'edrnsite.content/home-page.html'
    page_description = 'A content type specifically for the home page of the entire site'
    max_count = 1
    body = StreamField([
        ('title', blocks.TitleBlock()),
        ('section_cards', blocks.SiteSectionCardsBlock()),
        ('carousel', blocks.CarouselBlock()),
    ], null=True, blank=True, use_json_field=True)
    content_panels = Page.content_panels + [FieldPanel('body')]
    class Meta:
        verbose_name = 'home page'
        verbose_name_plural = 'home pages'


class SectionPage(MetadataPageMixin, Page):
    '''A page serving as a major section container.'''
    template = 'edrnsite.content/section-page.html'
    page_description = 'A page serving as a major section container'
    body = StreamField([
        ('title', blocks.TitleBlock()),
        ('section_cards', blocks.SiteSectionCardsBlock()),
    ], null=True, blank=True, use_json_field=True)
    content_panels = Page.content_panels + [FieldPanel('body')]
    class Meta:
        verbose_name = 'section page'
        verbose_name_plural = 'section pages'


class FlexPage(MetadataPageMixin, Page):
    '''A flexible page that has as stream of various fields.'''
    template = 'edrnsite.content/flex-page.html'
    page_description = 'Generic web page with a sequence of block content'
    body = StreamField([
        ('rich_text', wagtail_core_blocks.RichTextBlock(
            label='Rich Text',
            icon='doc-full',
            help_text='Richly formatted text',
        )),
        ('cards', blocks.CardsBlock()),
        ('table', blocks.TableBlock()),
        ('block_quote', blocks.BlockQuoteBlock(help_text='Block quote')),
        ('typed_table', blocks.TYPED_TABLE_BLOCK),
        ('carousel', blocks.CarouselBlock()),
        ('raw_html', wagtail_core_blocks.RawHTMLBlock(help_text='Raw HTML (use with care)')),
    ], null=True, blank=True, use_json_field=True)
    content_panels = Page.content_panels + [
        FieldPanel('body')
    ]
    search_fields = Page.search_fields + [
        index.SearchField('body'),
    ]
    class Meta(object):
        verbose_name = 'web page'
        verbose_name_plural = 'web pages'


class BaseEmailForm(Page):
    subpage_types = []
    intro = RichTextField(blank=True, help_text='Introductory text to appear above the form')
    outro = RichTextField(blank=True, help_text='Text to appear below the form')
    thank_you_text = RichTextField(blank=True, help_text='Gratitude to display after form submission')
    content_panels = AbstractEmailForm.content_panels + [
        FieldPanel('intro'),
        InlinePanel('form_fields', label='Form Fields ✍️'),
        FieldPanel('outro'),
        FieldPanel('thank_you_text'),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address', classname='col6', help_text='From whom this email will originate'),
                FieldPanel('to_address', classname='col6', help_text='Who should receive this email; commas in between multiple addresses')
            ]),
            FieldPanel('subject')
        ], 'Email')
    ]
    class Meta:
        abstract = True


class EmailForm(BaseEmailForm, AbstractEmailForm):
    template = 'edrnsite.content/email-form.html'
    landing_page_template = 'edrnsite.content/email-form-landing.html'
    page_description = 'Form that once submitted sends an email message'


class CapchaEmailForm(BaseEmailForm, WagtailCaptchaEmailForm):
    template = 'edrnsite.content/email-form.html'
    landing_page_template = 'edrnsite.content/email-form-landing.html'
    page_description = 'Form that once submitted sends an email message but also uses a CAPCTHA'


class LimitedFormField(AbstractFormField):
    '''This abstract form field removes the date and date/time choices.'''
    CHOICES = (
        ('singleline', _('Single line text')),
        ('multiline', _('Multi-line text')),
        ('email', _('Email')),
        ('number', _('Number')),
        ('url', _('URL')),
        ('checkbox', _('Checkbox')),
        ('checkboxes', _('Checkboxes')),
        ('dropdown', _('Drop down')),
        ('multiselect', _('Multiple select')),
        ('radio', _('Radio buttons')),
        ('hidden', _('Hidden field')),
    )
    field_type = models.CharField(verbose_name='Field Type', max_length=16, choices=CHOICES)
    class Meta:
        abstract = True
        ordering = ['sort_order']


class EmailFormField(LimitedFormField):
    page = ParentalKey(EmailForm, on_delete=models.CASCADE, related_name='form_fields')


class CaptchaEmailFormField(LimitedFormField):
    page = ParentalKey(CapchaEmailForm, on_delete=models.CASCADE, related_name='form_fields')


@register_snippet
class BoilerplateSnippet(models.Model):
    '''Legalese, disclaimer, or other text.'''
    bp_code = models.CharField(
        primary_key=True, max_length=80, blank=False, null=False, unique=True, help_text='Boilerplate ID code'
    )
    text = RichTextField(blank=False, null=False, help_text='Boilerplate rich text')
    panels = [FieldPanel('bp_code'), FieldPanel('text')]
    def __str__(self):
        return self.text

    class Meta:
        verbose_name = 'Boilerplate Snippet'
        verbose_name_plural = 'Boilerplate Snippets'


@register_snippet
class CertificationSnippet(models.Model):
    '''Certifying bodies and their URLs and labels.'''
    url = models.URLField(
        blank=False, null=False, primary_key=True, default='http://cert/location',
        help_text='URL to certifying body'
    )
    label = models.CharField(blank=False, null=False, max_length=80, default='label', help_text='What to call agency')
    description = models.TextField(blank=True, null=False, help_text='Summary of what the certifiying agency is for')
    panels = [FieldPanel('url'), FieldPanel('label'), FieldPanel('description')]
    def __str__(self):
        return self.label
