# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: Django custom template tags for sites'''

from django import template
from django.db.models.functions import Lower
from django.db.models.query import QuerySet
from django.utils.text import slugify
from wagtail.query import PageQuerySet
import logging

_logger = logging.getLogger(__name__)
register = template.Library()


@register.inclusion_tag('eke.knowledge/sites-by-type.html', takes_context=False)
def edrn_sites_by_type(sites: PageQuerySet) -> dict:
    return {'sites': sites.order_by(Lower('pi__title'))}


@register.inclusion_tag('eke.knowledge/sites-by-complex-and-arbitrary-groupings.html', takes_context=False)
def edrn_sites_organized_by_needlessly_complex_and_arbitrary_groups(
    label: str, sites: QuerySet, show_group_nums: bool
) -> dict:
    organs = {}
    for ogm in sites.all():
        organ, group_num = ogm.organ_name, ogm.group_num
        groups = organs.get(organ, {})
        group = groups.get(group_num, {'members': [], 'summary': '', 'target': slugify(f'{label}-{organ}-{group_num}')})
        group['members'].append({'site': ogm.site, 'pi': ogm.pi, 'role': ogm.role, 'member_type': ogm.member_type})
        # When finding the sumamry text for a group, pick the site that has the longest entry. In
        # general, all the sites in a group will have the same summary text, except the DMCC's group
        # has 3 sites but only one of which has summary text
        if len(ogm.site.specialty) > len(group['summary']):
            group['summary'] = ogm.site.specialty
        groups[group_num] = group
        organs[organ] = groups
    return {'organs': organs, 'show_group_nums': show_group_nums}
