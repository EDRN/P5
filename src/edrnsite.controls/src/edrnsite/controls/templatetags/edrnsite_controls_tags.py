# encoding: utf-8

'''🎛 EDRN Site Controls: tags.'''

from ..models import AnalyticsSnippet
from django import template
from django.utils.safestring import mark_safe


register = template.Library()


@register.simple_tag(takes_context=False)
def edrn_analytics(location: str) -> str:
    return mark_safe(''.join(AnalyticsSnippet.objects.filter(location=location).values_list('code', flat=True)))
