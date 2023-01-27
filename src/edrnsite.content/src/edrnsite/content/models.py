# encoding: utf-8

'''😌 EDRN site content's models.'''


from django.db import models
from django.utils.translation import gettext_lazy as _
from edrnsite.streams import blocks
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtailcaptcha.models import WagtailCaptchaEmailForm
from wagtail.core import blocks as wagtail_core_blocks
from wagtail.fields import RichTextField
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet
from wagtailmetadata.models import MetadataPageMixin


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
