# encoding: utf-8

'''🧫 EDRN Knowledge Environment biomarkers: biomarker-specific tags.'''


from ..biomarker import BiomarkerBodySystemCertification, BodySystemStudy
from ..constants import DepictableSections as ds
from django import template
from django.db.models.functions import Lower
from django.template.context import Context
from django.utils.text import slugify
from edrn.auth.views import authentication_context
from edrnsite.content.models import CertificationSnippet
from wagtail.admin.templatetags.wagtailuserbar import get_page_instance  # Feels odd importing from here


register = template.Library()


@register.inclusion_tag('eke.biomarkers/biomarker-basics.html', takes_context=True)
def biomarker_basics(context: Context) -> dict:
    '''For rendering the "Basics" tab of a biomarker view.'''
    biomarker = get_page_instance(context)
    return {
        'visible': ds.BASICS in context['visible_sections'],
        'aliases': biomarker.biomarker_aliases.all(),
        'description': biomarker.description,
        'qa_state': biomarker.qa_state,
        'biomarker_type': biomarker.biomarker_type,
        'hgnc_name': biomarker.hgnc_name,
        'request': context.get('request')
    }


@register.inclusion_tag('eke.biomarkers/biomarker-studies.html', takes_context=True)
def biomarker_studies(context: Context) -> dict:
    '''For rendering the "Studies" tab of a biomarker view.'''
    biomarker = get_page_instance(context)
    return {
        'visible': ds.STUDIES in context['visible_sections'],
        'protocols': biomarker.sorted_protocols,
        'request': context.get('request')        
    }


@register.inclusion_tag('eke.biomarkers/biomarker-resources.html', takes_context=True)
def biomarker_resources(context: Context) -> dict:
    '''For rendering the "Resources" tab of a biomarker view.'''
    biomarker = get_page_instance(context)
    return {
        'visible': ds.RESOURCES in context['visible_sections'],
        'resources': biomarker.sorted_resources,
        'request': context.get('request')        
    }


@register.inclusion_tag('eke.biomarkers/biomarker-publications.html', takes_context=True)
def biomarker_publications(context: Context) -> dict:
    '''For rendering the "Publications" tab of a biomarker view.'''
    biomarker = get_page_instance(context)
    return {
        'visible': ds.PUBLICATIONS in context['visible_sections'],
        'publications': biomarker.sorted_publications,
        'request': context.get('request')
    }


@register.inclusion_tag('eke.biomarkers/biomarker-data-collections.html', takes_context=True)
def biomarker_datacollections(context: Context) -> dict:
    '''For rendering the "Data Collections" tab of a biomarker view.'''
    biomarker = get_page_instance(context)
    return {
        'visible': ds.DATA_COL in context['visible_sections'],
        'data_collections': biomarker.sorted_science_data,
        'request': context.get('request')        
    }


@register.inclusion_tag('eke.biomarkers/biomarker-organs.html', takes_context=True)
def biomarker_organs(context: Context) -> dict:
    '''For rendering the organs tab of a biomarker view.'''
    biomarker = get_page_instance(context)
    organs = biomarker.biomarker_body_systems.all().order_by(Lower('title'))
    visible = False
    request = context.get('request')
    if request and request.user.is_authenticated:
        try:
            user_groups = frozenset(request.user.ldap_user.group_names)
            biomarker_groups = frozenset(biomarker.biomarker_access_groups.values_list('value', flat=True).distinct())
            visible = request.user.is_staff or request.user.is_superuser or len(user_groups & biomarker_groups) > 0
        except AttributeError:
            # Not an LDAP user
            pass
    return {
        'supplemental_visible': ds.SUPPLEMENTAL in context['visible_sections'],
        'biomarker': biomarker,
        'organs': [(slugify(i.title), i, i.qa_state == 'Accepted' or visible) for i in organs],
        'request': context.get('request')
    }


@register.inclusion_tag('eke.biomarkers/private-biomarker.html', takes_context=True)
def private_biomarker(context: Context) -> dict:
    '''For explaining why portions of a biomarker aren't visible.'''
    request = context.get('request')
    return authentication_context(request)


@register.inclusion_tag('eke.biomarkers/private-biomarkers.html', takes_context=True)
def private_biomarkers(context: Context) -> dict:
    request = context.get('request')
    return authentication_context(request)


@register.inclusion_tag('eke.biomarkers/certification.html', takes_context=False)
def biomarker_certification(certification: BiomarkerBodySystemCertification) -> dict:
    '''For rendering a laboratory certification made on a biomarker-organ relationship.'''
    url = certification.value
    context = {'url': url}
    snippet = CertificationSnippet.objects.filter(url__exact=url).first()
    if snippet:
        context['label'], context['description'] = snippet.label, snippet.description
    return context


@register.inclusion_tag('eke.biomarkers/organ-study-card.html', takes_context=False)
def organ_study_card(bss: BodySystemStudy) -> dict:
    '''For rendering a laboratory certification made on a biomarker-organ relationship.'''
    return {
        'title': bss.protocol.title,
        'url': bss.protocol.url,
        'organ': bss.bbs.title,
        'description': bss.protocol.description,
        'bss': bss,
    }
