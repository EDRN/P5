# encoding: utf-8

'''🎛 EDRN Site Controls: models.'''


from django.core.validators import MinValueValidator
from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import RichTextField
from wagtail.snippets.models import register_snippet


@register_snippet
class SocialMediaLink(models.Model):
    '''Social media link.'''
    name = models.CharField(blank=False, max_length=100, help_text='Name of the social media site', default='name')
    url = models.URLField(blank=False, help_text="Link to EDRN's presence on this site", default='https://site')
    bootstrap_icon = models.CharField(
        blank=False, max_length=32, help_text='Name of the icon to signify this site', default='emoji-smile'
    )
    enabled = models.BooleanField(default=True, help_text='Whether to include this in the footer')
    panels = [
        FieldPanel('name'),
        FieldPanel('url'),
        FieldPanel('bootstrap_icon'),
        FieldPanel('enabled')
    ]
    def __str__(self):
        return self.name


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
    entrez_api_key = models.CharField(
        null=False, blank=True, default='', max_length=64, help_text='Optional Entrez API key'
    )
    dmcc_url = models.URLField(
        default='https://www.compass.fhcrc.org/enterEDRN/?cl=3&amp;dl=0.9&amp;param1=dmcc&amp;extra_param=plin',
        null=False, help_text='URL to the DMCC "secure" site', blank=False
    )
    funding_cycle = models.CharField(default='Ⅴ', max_length=8, null=False, blank=False, help_text='EDRN Funding Cycle')
    site_wide_banner = RichTextField(blank=True, help_text='Banner to display site-wide at the top of every page')
    ip_address = models.CharField(
        default='unknown', max_length=40, null=False, blank=False, help_text='Last known source IP address of the portal'
    )
    ip_address_service = models.URLField(
        default='https://api.ipify.org', null=False, blank=False, help_text='API endpoint of IP address service'
    )
    override_version = models.CharField(
        default='', null=False, blank=True,
        help_text='Version number to override in footer; blank determines from software'
    )

    panels = [
        FieldPanel('in_development'),
        FieldPanel('entrez_email'),
        FieldPanel('entrez_id'),
        FieldPanel('entrez_api_key'),
        FieldPanel('dmcc_url'),
        FieldPanel('funding_cycle'),
        FieldPanel('site_wide_banner'),
        FieldPanel('ip_address'),
        FieldPanel('ip_address_service'),
        FieldPanel('override_version'),
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
    when_to_enable_ai = models.IntegerField(
        default=0, null=False, validators=[MinValueValidator(-1)],
        help_text='How many search results there must be to offer AI summary; zero will always use AI while -1 will turn it off'
    )
    bedrock_access_key = models.CharField(
        blank=False, null=False, help_text='AWS Access Key for Bedrock', default='key', max_length=192
    )
    bedrock_secret_key = models.CharField(
        blank=False, null=False, help_text='AWS Secret Access Key for Bedrock', default='key', max_length=192
    )
    bedrock_region = models.CharField(
        blank=False, null=False, help_text='AWS data center region', default='us-west-2', max_length=12
    )
    system_prompt = models.CharField(
        blank=False, null=False, help_text='System prompt to present for search result summaries', max_length=1000,
        default='Act as a search assistant for the Early Detection Research Network, summarizing voluminous search results into easily digestible summaries.'
    )
    panels = [
        MultiFieldPanel(children=(
            FieldPanel('results_per_page'),
            FieldPanel('orphans'),
            FieldPanel('surrounding'),
            FieldPanel('ends')
        ), heading='Result Display'),
        MultiFieldPanel(children=(
            FieldPanel('when_to_enable_ai'),
            FieldPanel('system_prompt'),
            FieldPanel('bedrock_access_key'),
            FieldPanel('bedrock_secret_key'),
            FieldPanel('bedrock_region')
        ), heading='AI')
    ]
