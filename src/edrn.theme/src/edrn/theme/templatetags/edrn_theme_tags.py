# encoding: utf-8

'''🎨 EDRN Theme: Django tags.'''

from django.template.context import Context
from django import template
from wagtailmenus.models import FlatMenu
from wagtailmenus.templatetags.menu_tags import flat_menu
from django.utils.safestring import mark_safe
from importlib import import_module

register = template.Library()


@register.inclusion_tag('edrn.theme/footer-menus.html', takes_context=True)
def edrn_footer_menus(context: Context) -> dict:
    menus = FlatMenu.objects.filter(handle__startswith='footer-').order_by('title')
    return {'menus': menus, 'original_context': context}


@register.simple_tag(takes_context=True)
def request_restoring_flat_menu(context: Context, original_context: Context, **kwargs):
    context['request'] = original_context['request']
    rc = flat_menu(context, **kwargs)
    return rc


@register.simple_tag(takes_context=False)
def edrn_portal_version() -> str:
    version = None
    try:
        module = import_module('edrnsite.policy')  # No circular dependency here
        version = getattr(module, 'VERSION', None)
    except ModuleNotFoundError:
        pass
    if not version:
        # Okay, just use the theme's version
        from edrn.theme import VERSION as version
    return mark_safe(str(version))
