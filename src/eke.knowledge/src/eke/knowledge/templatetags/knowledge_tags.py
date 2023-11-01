# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: Django custom template tags for knowledge.'''

from ..protocols import Protocol
from ..sciencedata import DataCollection
from ..sites import Site, Person
from django import template
from django.template.context import Context
from django.utils.safestring import mark_safe
from edrn.collabgroups.models import CollaborativeGroupSnippet
from eke.biomarkers.biomarker import Biomarker
from wagtail.admin.templatetags.wagtailuserbar import get_page_instance  # Feels odd importing from here
import logging

_logger = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag(takes_context=True)
def faceted_results(context: Context) -> str:
    page, request = get_page_instance(context), context.get('request')
    if page is None:
        _logger.warning('🚨 In faceted_results tag, there is no page or self object')
        return ''
    if request is None:
        _logger.warning('🚨 In faceted_results tag, there is no request object')
        return ''
    return mark_safe(page.faceted_markup(request))


@register.simple_tag(takes_context=False)
def protocol_counts(protocol: Protocol, statistic: str) -> str:
    result = '«unknown»'
    if statistic == 'biomarkers':
        result = str(Biomarker.objects.filter(protocols=protocol).public().live().count())
    elif statistic == 'data':
        result = str(DataCollection.objects.filter(generating_protocol=protocol).live().count())
    return mark_safe(result)


def _get_terms(context: Context, vocab_name: str) -> list:
    page = get_page_instance(context)
    if page is None:
        _logger.warning('🚨 In knowledge_tags, there is no page or self object; using an empty vocabulary')
        return []
    else:
        return page.get_vocabulary(vocab_name)


@register.inclusion_tag('eke.knowledge/faceted-vocab-selector.html', takes_context=True)
def faceted_vocab_selector(context: Context, vocab_name: str, label=None) -> dict:
    terms = _get_terms(context, vocab_name)
    if label is None: label = vocab_name.capitalize()
    return {'label': label, 'terms': terms, 'vocab_name': vocab_name}


@register.inclusion_tag('eke.knowledge/faceted-vocab-checks.html', takes_context=True)
def faceted_vocab_checks(context: Context, vocab_name: str, label=None) -> dict:
    terms = _get_terms(context, vocab_name)
    if label is None: label = vocab_name.capitalize()
    return {'label': label, 'terms': terms, 'vocab_name': vocab_name}


@register.inclusion_tag('eke.knowledge/faceted-vocab-checks.html', takes_context=False)
def faceted_edrn_collab_group_checks(label=None) -> dict:
    if label is None: label = 'Collaborative Groups'
    terms = [str(i) for i in CollaborativeGroupSnippet.objects.all()]
    return {'label': label, 'terms': terms, 'vocab_name': 'collab_group'}


@register.inclusion_tag('eke.knowledge/faceted-vocab-selector.html', takes_context=False)
def faceted_edrn_collab_group_selector(label=None) -> dict:
    if label is None: label = 'Collaborative Groups'
    terms = [str(i) for i in CollaborativeGroupSnippet.objects.all()]
    return {'label': label, 'terms': terms, 'vocab_name': 'collab_group'}


@register.inclusion_tag('eke.knowledge/member-finder-member-types.html', takes_context=True)
def member_finder_member_types(context: Context) -> dict:
    return {'types': Site.objects.values_list('memberType', flat=True).distinct().order_by('memberType')}


@register.inclusion_tag('eke.knowledge/member-finder-sites.html', takes_context=True)
def member_finder_sites(context: Context) -> dict:
    return {'sites': Site.objects.values_list('title', flat=True).distinct().order_by('title')}


@register.inclusion_tag('eke.knowledge/member-finder-pis.html', takes_context=True)
def member_finder_pis(context: Context) -> dict:
    return {'pis': Person.objects.filter(pk__in=Site.objects.values_list('pi')).order_by('title')}
