# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: Django custom template filters for knowledge.'''

from django import template
from wagtail.models import Orderable
import logging, humanize

_logger = logging.getLogger(__name__)
register = template.Library()


@register.filter
def knowledge_labelize(value: str) -> str:
    return value.capitalize().replace('_', ' ')


@register.filter
def friendly_duration(value: str) -> str:
    if value is None:
        return 'Unknown 🤔'
    return humanize.precisedelta(value)


@register.filter
def knowledge_value_joined(items: Orderable, separator=', ') -> str:
    '''Render EKE values.

    For an EDRN Knowledge Environment related field where the 1-to-many relation is simply a model
    object instance with an RDF-ingested text ``value``, render the individual valus with ``separator``
    separating each.
    '''
    return separator.join([i.value for i in items.all()])


@register.filter
def replace_brs(value: str) -> str:
    '''Certain protocols have abstracts with tons of <br>s in them. Change those to spaces.'''
    return value.replace('&#060;br&#062;', ' ')


@register.filter
def strip_midnight(value: str) -> str:
    '''Drop the "12:00AM" that the DMCC insists on putting in protocol start & finish dates.'''
    return value.replace('12:00AM', '')
