# encoding: utf-8

'''😌 EDRN site content's models.'''


from ._dataset_metadata_form import DatasetMetadataFormPage  # noqa: F401
from ._metadata_collection_form import MetadataCollectionFormPage  # noqa: F401
from ._spec_ref_set_form import SpecimenReferenceSetRequestFormPage  # noqa: F401
from ._explorer import CDEExplorerPage, CDEExplorerObject, CDEExplorerAttribute, CDEPermissibleValue  # noqa: F401
from django import forms
from django.conf import settings
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from edrnsite.streams import blocks
from modelcluster.fields import ParentalKey
from wagtail import blocks as wagtail_core_blocks
from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
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
    preview_modes = []
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
            form = form_class(request.POST, page=self)
            if form.is_valid():
                params = {'page': self, **self.process_submission(form)}
                return render(request, self.get_landing_page(), params)
        else:
            form = form_class(initial=self.get_initial_values(request), page=self)
        self._bootstrap(form)
        return render(request, 'edrnsite.content/form.html', {'page': self, 'form': form})  # Fix this

    class Meta:
        abstract = True


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


class CaptchaEmailForm(BaseEmailForm, WagtailCaptchaEmailForm):
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
    page = ParentalKey(CaptchaEmailForm, on_delete=models.CASCADE, related_name='form_fields')


# Turns out we are not going to use this
# class SantiagoTaxonomyPage(Page):
#     page_description = "A page that displays an interactive taxonomy using Santiago's D3 JavaScript"
#     template = 'edrnsite.content/taxonomy-page.html'
#     taxonomy = models.ForeignKey(
#         'wagtaildocs.Document', null=True, blank=False, verbose_name='Taxonomy JavaScript file',
#         on_delete=models.SET_NULL, related_name='taxonomy_page')
#     content_panels = Page.content_panels + [FieldPanel('taxonomy')]


# Turns out we are not going to use this
# class TreeExplorerPage(Page):
#     page_description = 'A page that displays an interactive explorer-like interface'
#     template = 'edrnsite.content/tree-explorer.html'
#     DEMO_MODES = [
#         ('compact', 'Compact'),
#         ('full', 'Full')
#     ]
#     demo_mode = models.CharField(max_length=7, null=False, blank=False, default='compact', choices=DEMO_MODES)
#     content_panels = [FieldPanel('demo_mode')]


# Delete this# Turns out we are not going to use this
# class MetadataObject(Page):
#     page_description = 'A kind of object defined with metadata attributes'
#     template = 'edrnsite.content/metadata-object.html'
#     content_panels = []


# Delete this# Turns out we are not going to use this
# class MetadataSet(Page):
#     page_description = 'A page that shows common data elements as part of a set of metadata'
#     template = 'edrnsite.content/metadata-page.html'
#     content_panels = []
#     subpage_types = [MetadataObject]


class PostmanAPIPage(Page):
    page_description = 'A page that shows an Application Programmer Interface specified by Postman and formatted by Postmanerator'
    template = 'edrnsite.content/postman-api-page.html'
    postman = models.TextField(null=False, blank=False, help_text='Postman JSON Export')
    swagger = models.TextField(null=False, blank=False, help_text='OpenAPI YAML Conversion')
    postmanerator = models.TextField(null=False, blank=True, help_text='Postmanerator documentation using EDRN Portal Theme')
    content_panels = Page.content_panels + [FieldPanel('postman'), FieldPanel('swagger'), FieldPanel('postmanerator')]

    def serve(self, request: HttpRequest) -> HttpResponse:
        if request.GET.get('download'):
            response = HttpResponse(charset=settings.DEFAULT_CHARSET)
            fn_prefix = slugify(self.title)
            if request.GET.get('download') == 'postman':
                response.headers['Content-Type'] = 'application/json'
                response.headers['Content-Disposition'] = f'attachment; filename="{fn_prefix}.json"'
                response.content = self.postman.encode(settings.DEFAULT_CHARSET)
            elif request.GET.get('download') == 'openapi':
                response.headers['Content-Type'] = 'application/yaml'  # Note: this mime type is currently in draft
                response.headers['Content-Disposition'] = f'attachment; filename="{fn_prefix}.yaml"'
                response.content = self.swagger.encode(settings.DEFAULT_CHARSET)
            else:
                raise ValueError('Expected "postman" or "openapi"')
            return response
        else:
            return super().serve(request)


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
