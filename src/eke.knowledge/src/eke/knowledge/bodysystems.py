# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: body systems (organs).'''

from .knowledge import KnowledgeObject, KnowledgeFolder
from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.models import Orderable


class BodySystem(KnowledgeObject):
    '''A body system is an organ or related system of organs in the human body.'''
    template = KnowledgeObject.template
    search_auto_update = False
    parent_page_types = ['ekeknowledge.BodySystemIndex']


class BodySystemIndex(KnowledgeFolder):
    '''A body system index is a container for body systems.'''
    subpage_types = [BodySystem]
    search_auto_update = False
    template = 'eke.knowledge/knowledge-folder.html'
    class RDFMeta:
        ingestor = KnowledgeFolder.RDFMeta.ingestor
        types = {'http://edrn.nci.nih.gov/rdf/types.rdf#BodySystem': BodySystem}


class Organ(Orderable):
    '''An organ of the body.

    This is different from BodySystem in that the former is controlled by the DMCC's vocabulary and RDF
    descriptions of organs, while this class is just plain text that names an organ. Despite having such
    a well-curated vocabulary of organs (BodySystem), in practice no one used it, and preferred just to
    capture text names. That's what this class is for.

    Subclasses should add a ``page`` attribute as a ``ParentalKey`` that links these plain text organs
    to their comprising classes.
    '''
    value = models.CharField(max_length=255, blank=False, null=False, default='Name', help_text='Name of the organ')
    panels = [FieldPanel('value')]
