# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: Django custom template tags for sites'''

from django import template
from django.db.models.functions import Lower
from django.db.models.query import QuerySet
from wagtail.query import PageQuerySet
import logging

_logger = logging.getLogger(__name__)
register = template.Library()


@register.inclusion_tag('eke.knowledge/sites-by-type.html', takes_context=False)
def edrn_sites_by_type(sites: PageQuerySet) -> dict:
    return {'sites': sites.order_by(Lower('pi__title'))}


@register.inclusion_tag('eke.knowledge/sites-by-complex-and-arbitrary-groupings.html', takes_context=False)
def edrn_sites_organized_by_needlessly_complex_and_arbitrary_groups(sites: QuerySet, show_group_nums: bool) -> dict:
    organs = {}
    for ogm in sites.all():
        organ, group_num = ogm.organ_name, ogm.group_num
        groups = organs.get(organ, {})
        group = groups.get(group_num, [])
        group.append({'site': ogm.site, 'pi': ogm.pi, 'role': ogm.role, 'member_type': ogm.member_type})
        groups[group_num] = group
        organs[organ] = groups
    return {'organs': organs, 'show_group_nums': show_group_nums}
