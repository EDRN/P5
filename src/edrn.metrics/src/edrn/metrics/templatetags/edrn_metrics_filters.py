# encoding: utf-8

'''📐 EDRN metrics: filters.'''

from django import template


register = template.Library()


@register.filter
def strip_timezone(value: str) -> str:
    return value[:-6]
