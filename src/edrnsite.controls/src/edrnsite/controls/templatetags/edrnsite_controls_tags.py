# encoding: utf-8

'''🎛 EDRN Site Controls: tags.'''

from ..models import AnalyticsSnippet, Informatics
from django import template
from django.utils.safestring import mark_safe
from wagtail.models import Site


register = template.Library()


@register.simple_tag(takes_context=False)
def edrn_analytics(location: str) -> str:
    return mark_safe(''.join(AnalyticsSnippet.objects.filter(location=location).values_list('code', flat=True)))


@register.simple_tag(takes_context=False)
def edrn_funding_cycle() -> str:
    informatics = Informatics.for_site(Site.objects.filter(is_default_site=True).first())
    return informatics.funding_cycle
