# encoding: utf-8

'''😌 EDRN site content custom template tags: the ``edrnsite_content`` library.'''


from ..models import BoilerplateSnippet, CDEExplorerObject, CDEExplorerAttribute
from django import template
from django.utils.text import slugify
from wagtail.templatetags.wagtailcore_tags import richtext

register = template.Library()


@register.simple_tag(takes_context=False)
def edrn_boilerplate(bp_code: str) -> str:
    bp = BoilerplateSnippet.objects.filter(bp_code__exact=bp_code).first()
    return richtext(bp.text) if bp else ''


@register.inclusion_tag('edrnsite.content/cde-node.html', takes_context=False)
def render_cde_node(node: CDEExplorerObject) -> dict:
    return {
        'name': node.name,
        'description': node.description,
        'attributes': node.attributes.all(),
        'children': node.children.all().order_by('name')
    }


@register.inclusion_tag('edrnsite.content/cde-attribute-button.html', takes_context=False)
def render_cde_attribute_button(attribute: CDEExplorerAttribute) -> dict:
    return {
        'id': f'cde-{slugify(attribute.obj.name)}-{slugify(attribute.text)}',
        'text': attribute.text,
        'required': attribute.required == 'Required',
        'inheritance': attribute.inheritance
    }


@register.inclusion_tag('edrnsite.content/cde-attribute-canvases.html', takes_context=False)
def render_cde_attribute_canvases(node: CDEExplorerObject) -> dict:
    return {
        'attributes': node.attributes.all(),
        'children': node.children.all()
    }


@register.inclusion_tag('edrnsite.content/cde-attribute-canvas.html', takes_context=False)
def render_cde_attribute_canvas(attribute: CDEExplorerAttribute) -> dict:
    return {
        'id': f'cde-{slugify(attribute.obj.name)}-{slugify(attribute.text)}',
        'text': attribute.text,
        'definition': attribute.definition,
        'required': attribute.required,
        'data_type': attribute.data_type,
        'note': attribute.explanatory_note,
        'pvs': attribute.permissible_values.all(),
        'inheritance': attribute.inheritance
    }
