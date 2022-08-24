# encoding: utf-8

from .bodysystems import BodySystem
from .knowledge import KnowledgeObject, KnowledgeFolder
from .rdf import RDFAttribute, RelativeRDFAttribute
from django.db import models
from modelcluster.fields import ParentalManyToManyField
from wagtail.admin.panels import FieldPanel


def _schema(element: str) -> str:
    '''Make a full EDRN predicate URI for the given ``element``.

    Only the diseases RDF uses a **different** prefix than all our other RDF 😱
    '''
    return 'http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#' + element


class Disease(KnowledgeObject):
    '''A disease is an affliction, ailment, disorder, etc., of a body system.'''
    template = 'eke.knowledge/disease.html'
    parent_page_types = ['ekeknowledge.DiseaseIndex']
    search_auto_update = False
    icd9Code = models.CharField(
        'ICD9', blank=True, null=False, max_length=10,
        help_text='International Statistical Classifiction of Disease Code (version 9)'
    )
    icd10Code = models.CharField(
        'ICD10', blank=True, null=False, max_length=20,
        help_text='International Statistical Classifiction of Disease Code (version 10)'
    )
    affectedOrgans = ParentalManyToManyField(
        BodySystem, blank=True, verbose_name='Affected Organs', related_name='diseases'
    )
    content_panels = KnowledgeObject.content_panels + [
        FieldPanel('icd9Code'),
        FieldPanel('icd10Code'),
        FieldPanel('affectedOrgans'),
    ]
    class RDFMeta:
        fields = {
            _schema('icd9'): RDFAttribute('icd9Code', scalar=True),
            _schema('icd10'): RDFAttribute('icd10Code', scalar=True),
            _schema('bodySystemsAffected'): RelativeRDFAttribute('affectedOrgans', scalar=False),
            **KnowledgeObject.RDFMeta.fields
        }


class DiseaseIndex(KnowledgeFolder):
    '''A disease index is a container for diseases.'''
    subpage_types = [Disease]
    template = 'eke.knowledge/knowledge-folder.html'
    class RDFMeta:
        ingestor = KnowledgeFolder.RDFMeta.ingestor
        types = {'http://edrn.nci.nih.gov/rdf/types.rdf#Disease': Disease}
