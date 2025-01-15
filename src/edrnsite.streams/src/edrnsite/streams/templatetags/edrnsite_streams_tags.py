# encoding: utf-8

'''🦦 EDRN Site streams: template tags.'''

from ..models import DataElementExplorerAttribute, DataElementExplorerObject
from django import template
from django.utils.safestring import mark_safe
from django.utils.text import slugify

register = template.Library()


@register.simple_tag(takes_context=False)
def mark_external_link(url: str) -> str:
    marker = '<i class="bi bi-box-arrow-up-right"></i> ' if url.startswith('http') else ''
    return mark_safe(marker)


@register.inclusion_tag('edrnsite.streams/de-roots.html', takes_context=False)
def render_de_roots(spreadsheet_id: str) -> dict:
    return {'root_objects': DataElementExplorerObject.objects.filter(spreadsheet_id=spreadsheet_id)}


@register.inclusion_tag('edrnsite.streams/de-root-canvases.html', takes_context=False)
def render_all_de_attribute_canvases(spreadsheet_id: str) -> dict:
    return {'root_objects': DataElementExplorerObject.objects.filter(spreadsheet_id=spreadsheet_id)}


@register.inclusion_tag('edrnsite.streams/de-node.html', takes_context=False)
def render_de_node(node: DataElementExplorerObject) -> dict:
    return {
        'name': node.name,
        'description': node.description,
        'stewardship': node.stewardship,
        'attributes': node.attributes.all(),
        'children': node.children.all().order_by('name')
    }


@register.inclusion_tag('edrnsite.streams/de-attribute-button.html', takes_context=False)
def render_de_attribute_button(attribute: DataElementExplorerAttribute) -> dict:
    return {
        'id': f'de-{slugify(attribute.obj.name)}-{slugify(attribute.text)}',
        'text': attribute.text,
        'required': attribute.required == 'Required',
        'inheritance': attribute.inheritance
    }


@register.inclusion_tag('edrnsite.streams/de-attribute-canvases.html', takes_context=False)
def render_de_attribute_canvases(node: DataElementExplorerObject) -> dict:
    return {
        'attributes': node.attributes.all(),
        'children': node.children.all()
    }


@register.inclusion_tag('edrnsite.streams/de-attribute-canvas.html', takes_context=False)
def render_de_attribute_canvas(attribute: DataElementExplorerAttribute) -> dict:
    return {
        'id': f'de-{slugify(attribute.obj.name)}-{slugify(attribute.text)}',
        'text': attribute.text,
        'definition': attribute.definition,
        'required': attribute.required,
        'data_type': attribute.data_type,
        'note': attribute.explanatory_note,
        'pvs': attribute.permissible_values.all(),
        'inheritance': attribute.inheritance
    }
