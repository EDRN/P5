# encoding: utf-8

'''🦦 EDRN Site streams: template tags.'''

from django import template
from django.utils.safestring import mark_safe


register = template.Library()


@register.simple_tag(takes_context=False)
def mark_external_link(url: str) -> str:
    marker = '<i class="bi bi-box-arrow-up-right"></i> ' if url.startswith('http') else ''
    return mark_safe(marker)
