# encoding: utf-8

'''😌 EDRN site content's models.'''


from django.db import models
from edrnsite.streams import blocks
from wagtail.admin.panels import FieldPanel
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
    body = StreamField([
        ('rich_text', wagtail_core_blocks.RichTextBlock(
            label='Rich Text',
            icon='doc-full',
            help_text='Richly formatted text',
        )),
        ('cards', blocks.CardsBlock()),
        ('table', blocks.TableBlock()),
        ('block_quote', blocks.BlockQuoteBlock(help_text='Block quote')),
        ('typed_table', blocks.TypedTableBlock([
            ('text', wagtail_core_blocks.CharBlock(help_text='Plain text cell')),
            ('rich_text', wagtail_core_blocks.RichTextBlock(help_text='Rich text cell')),
            ('numeric', wagtail_core_blocks.FloatBlock(help_text='Numeric cell')),
            ('integer', wagtail_core_blocks.IntegerBlock(help_text='Integer cell')),
            ('page', wagtail_core_blocks.PageChooserBlock(help_text='Page within the site')),
        ])),
        ('carousel', blocks.CarouselBlock()),
        ('raw_html', wagtail_core_blocks.RawHTMLBlock(help_text='Raw HTML (use with care)')),
    ], null=True, blank=True, use_json_field=True)
    content_panels = Page.content_panels + [
        FieldPanel('body')
    ]
    class Meta(object):
        verbose_name = 'web page'
        verbose_name_plural = 'web pages'


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
