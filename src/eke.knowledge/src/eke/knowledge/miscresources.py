# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: miscelanoues resources.'''

from .knowledge import KnowledgeObject, KnowledgeFolder
from .utils import Ingestor as BaseIngestor
import rdflib


# The Focus Biomarker Database is dumb: it doesn't use a standard Dublin Core "title"; it uses this monstrosity:
_titlePredicateURI = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Description')


class MiscellaneousResource(KnowledgeObject):
    '''A miscellaneous resource is just a URL with a description.'''
    template = 'eke.knowledge/misc-resource.html'
    parent_page_types = ['ekeknowledge.MiscellaneousResourceIndex']
    search_auto_update = False
    search_fields = []  # 🔮 We should remove this as it causes a warning at startup, but we want these cleared from ES
    page_description = 'Any resource with a URL'
    class RDFMeta:
        fields = {}


class MiscellaneousResourceIndex(KnowledgeFolder):
    '''A miscellaneous resource index is a container for Miscellaneous resources.'''
    subpage_types = [MiscellaneousResource]
    template = 'eke.knowledge/knowledge-folder.html'
    page_description = 'Container for miscellaneous resources'
    class RDFMeta:
        ingestor = 'eke.knowledge.miscresources.Ingestor'
        types = {
            'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#ExternalResource': MiscellaneousResource
        }


class Ingestor(BaseIngestor):
    '''Custom RDF ingestor for miscellaneous resources.

    This is needed because miscellaneous resources from the Focus Biomarker Database doesn't use
    Dublin Core for titles of objects.
    '''
    def getTitle(self, uri: rdflib.URIRef, predicates: dict) -> str:
        title = predicates.get(_titlePredicateURI, [''])[0]
        return title if title else '«No title ("Description") was specified for this resource»'
