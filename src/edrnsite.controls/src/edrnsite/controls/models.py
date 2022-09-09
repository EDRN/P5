# encoding: utf-8

'''🎛 EDRN Site Controls: models.'''


from django.core.validators import MinValueValidator
from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.snippets.models import register_snippet


@register_setting
class SocialMedia(BaseSiteSetting):
    '''Social media controls.'''
    facebook  = models.URLField(blank=True, help_text="URL to NCI's Facebook page")
    twitter   = models.URLField(blank=True, help_text="URL to DCP's Twitter profile")
    panels    = [
        FieldPanel('facebook'),
        FieldPanel('twitter'),
    ]


@register_snippet
class AnalyticsSnippet(models.Model):
    '''JavaScript support for website analytics.'''
    LOCATIONS = [('h', 'Header'), ('b', 'Bottom')]
    location = models.CharField(
        max_length=1, choices=LOCATIONS, default='b', blank=False, null=False,
        help_text='Where to inject this; in the <head> or at the bottom before the closing </body>'
    )
    code = models.TextField(
        blank=False, null=False, default='<script></script>', help_text='JavaScript analytics code'
    )
    panels = [FieldPanel('location'), FieldPanel('code')]
    def __str__(self):
        return self.code


# 🤔 Do we want to do this?
# @register_snippet
# class Portlet(models.Model):
#     '''Some text for placement on the EDRN site somewhere.'''
#     location = models.CharField(max_length=10, blank=False, null=False, default='location', primary_key=True)
#     # In case we need multiple portlets in a location:
#     # order = models.PositiveIntegerField(default=0, null=False, help_text='In what order to show this portlet')
#     text = RichTextField(blank=True, null=False, help_text='Portlet text')
#     panels = [FieldPanel('location'), FieldPanel('text')]
#     def __str__(self):
#         return self.text
#     class Meta:
#         verbose_name = 'Portlet'
#         verbose_name_plural = 'Portlets'


@register_setting
class Informatics(BaseSiteSetting):
    '''Informatics controls.'''
    in_development = models.BooleanField(default=True, null=False, help_text='True if this site is in development')
    entrez_email = models.EmailField(default='sean.kelly@nih.gov', null=False, help_text='Entrez registered user email')
    entrez_id = models.CharField(
        default='edrn-portal', null=False, max_length=64, help_text='Entrez (PubMed API) tool identification'
    )
    dmcc_url = models.URLField(
        default='https://www.compass.fhcrc.org/enterEDRN/?cl=3&amp;dl=0.9&amp;param1=dmcc&amp;extra_param=plin',
        null=False, help_text='URL to the DMCC "secure site"', blank=False
    )
    panels = [
        FieldPanel('in_development'),
        FieldPanel('entrez_email'),
        FieldPanel('entrez_id'),
    ]


@register_setting
class Search(BaseSiteSetting):
    '''Search controls.'''
    results_per_page = models.IntegerField(
        default=20, null=False, validators=[MinValueValidator(1)],
        help_text='How many hits to show per page on search'
    )
    orphans = models.IntegerField(
        default=3, null=False, validators=[MinValueValidator(0)],
        help_text='How many orphans to avoid having on a lone search page'
    )
    surrounding = models.IntegerField(
        default=3, null=False, validators=[MinValueValidator(0)],
        help_text='How many pages to show surrounding the active page in search pagination outside of elision',
    )
    ends = models.IntegerField(
        default=2, null=False, validators=[MinValueValidator(0)],
        help_text='How many pages to show at the start and end of search pagination regardless of elision',
    )
    panels = [
        FieldPanel('results_per_page'),
        FieldPanel('orphans'),
        FieldPanel('surrounding'),
        FieldPanel('ends')
    ]
