# encoding: utf-8

'''😌 EDRN site content custom template tags: the ``edrnsite_content`` library.'''


from ..models import BoilerplateSnippet
from django import template
from wagtail.templatetags.wagtailcore_tags import richtext


register = template.Library()


@register.simple_tag(takes_context=False)
def edrn_boilerplate(bp_code: str) -> str:
    bp = BoilerplateSnippet.objects.filter(bp_code__exact=bp_code).first()
    return richtext(bp.text) if bp else ''
