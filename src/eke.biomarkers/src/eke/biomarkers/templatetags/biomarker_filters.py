# encoding: utf-8

'''🧫 EDRN Knowledge Environment biomarkers: biomarker-specific filters.'''


from ..biomarker import Biomarker
from django import template
from django.db.models.functions import Lower

register = template.Library()


@register.filter
def organs_for_biomarker(value: Biomarker) -> list:
    '''Yield a list of all the organs (body systems) for which this biomarker is an indicator for disease.'''
    return value.biomarker_body_systems.values_list('title', flat=True).distinct().order_by(Lower('title'))


@register.filter
def phases_for_biomarker(value: Biomarker) -> list:
    '''Yield a list of all the phases of biomarker development for the ``value`` biomarker.'''
    phases, fallback = set(), set()
    for bbs in value.biomarker_body_systems.all():
        phase = bbs.phase
        if phase is not None:
            fallback.add(phase)
        for bss in bbs.body_system_studies.all():
            phase = bss.phase
            if phase is not None:
                phases.add(bss.phase)
    phases = phases if phases else fallback
    return sorted(list(phases))
