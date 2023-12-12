# encoding: utf-8

'''🎨 EDRN Theme: Django tags.'''

from django import template
from django.template.context import Context
from django.utils.safestring import mark_safe
from edrnsite.controls.models import SocialMediaLink
from importlib import import_module
from wagtailmenus.models import FlatMenu
from wagtailmenus.templatetags.menu_tags import flat_menu

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


@register.inclusion_tag('edrn.theme/social-media.html', takes_context=False)
def edrn_social_media_links() -> dict:
    links = SocialMediaLink.objects.all().filter(enabled=True).order_by('name')
    return {'links': [{'name': link.name, 'url': link.url, 'icon': link.bootstrap_icon} for link in links]}
