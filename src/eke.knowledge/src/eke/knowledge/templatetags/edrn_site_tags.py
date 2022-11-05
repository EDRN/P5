# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: Django custom template tags for sites'''

from django import template
from django.db.models.functions import Lower
import logging

_logger = logging.getLogger(__name__)
register = template.Library()


@register.inclusion_tag('eke.knowledge/biomarker-developmental-laboratories.html', takes_context=False)
def biomarker_developmental_laboratories(bdls: list) -> dict:
    '''Return the BDLs with their organs and proposals.

    This returns a sequence of dictionaries with a ``title`` key that names an organ and a
    ``proposal_groups`` key that is a sequence of dictionaries with a ``title`` key that is the name
    of a proposal, a ``sites`` key that is a sequence of ``Site`` objects, a ``speciality`` that gives
    the program information, and ``cid`` that can be used to identify a collapsbile HTML section where
    the speciality can be expanded. The proposals are sorted lexicographically—and the organ names are too.
    '''
    by_organ, cid = {}, 0
    for site in bdls:
        organs = [i.value for i in site.organs.all()]
        if not organs:
            organs = ['(No organ-specific research)']
        for organ_name in organs:
            proposals = by_organ.get(organ_name, {})
            sites = proposals.get(site.proposal, [])
            sites.append(site)
            proposals[site.proposal] = sites
            by_organ[organ_name] = proposals
    organs = []
    for organ_name, proposals in by_organ.items():
        prop_group = []
        for proposal_name, sites in proposals.items():
            prop_group.append(dict(title=proposal_name, sites=sites, specialty=sites[0].specialty, cid=f'summary{cid}'))
            cid += 1
        prop_group.sort(key=lambda i: i['title'])
        organs.append(dict(title=organ_name, proposal_groups=prop_group))
    organs.sort(key=lambda i: i['title'])            
    return {'bdls': organs}


@register.inclusion_tag('eke.knowledge/sites-by-type.html', takes_context=False)
def edrn_sites_by_type(sites: list, show_organs: bool) -> dict:
    by_proposal = {}
    for site in sites.order_by(Lower('proposal')).order_by(Lower('pi__title')):
        specialty = site.specialty if site.specialty and site.specialty != ',' else None  # DMCC data quality = 🤢
        sites = by_proposal.get(specialty, [])
        sites.append(site)
        by_proposal[specialty] = sites
    proposal_groups, cid = [], 0
    for specialty, sites in by_proposal.items():
        proposal_groups.append({'specialty': specialty, 'sites': sites, 'cid': f'speciality{cid}'})
        cid += 1
    return dict(proposal_groups=proposal_groups, show_organs=show_organs)
