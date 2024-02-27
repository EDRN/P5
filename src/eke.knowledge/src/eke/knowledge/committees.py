# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: committees.'''


from .knowledge import KnowledgeFolder
from .sites import Person
from .utils import Ingestor as BaseIngestor
from django.core.exceptions import ValidationError
from django.db.models.functions import Lower
from django.http import HttpRequest
from wagtail.models import Page
import logging, urllib.parse, rdflib

_logger = logging.getLogger(__name__)

_chair             = rdflib.term.URIRef('http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#chair')
_co_chair          = rdflib.term.URIRef('http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#coChair')
_member            = rdflib.term.URIRef('http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#member')
_project_scientist = rdflib.term.URIRef('urn:edrn:rdf:predicates:project_scientist')
_program_officer   = rdflib.term.URIRef('urn:edrn:rdf:predicates:program_officer')
_consultant        = rdflib.term.URIRef('http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#consultant')

# Note: at one time Heather Kincaid was the sole "consultant" in the RDF; there are none now,
# however I'm leaving the predicate ↑ in here in case any more show up. Here in P5 we treat
# them as just additional members.


class Ingestor(BaseIngestor):
    '''Custom RDF ingestor for committees.

    Ingest for committees is totally different so we completely override ingest and take over.
    '''
    def ingest(self):
        from edrn.collabgroups.models import Committee
        _logger.debug('Starting ingest for %s', self.folder)
        if not self.folder.ingest:
            _logger.info('Ingest disabled for %r, skipping it', self.folder)
        statements = self.readRDF()
        for uri, predicates in statements.items():
            id_number = urllib.parse.urlparse(uri).path.split('/')[-1]
            committee = Committee.objects.filter(id_number=id_number).first()
            if committee is None: continue
            new_title = predicates.get(rdflib.DCTERMS.title, [''])[0].strip()
            if new_title:
                committee.title = new_title
            new_chair = predicates.get(_chair, [None])[0]
            if new_chair:
                person = Person.objects.filter(identifier=new_chair).first()
                if person:
                    committee.chair = person
            new_co_chair = predicates.get(_co_chair, [None])[0]
            if new_co_chair:
                person = Person.objects.filter(identifier=new_co_chair).first()
                if person:
                    committee.co_chair = person
            new_members = set(predicates.get(_member, [])) | set(predicates.get(_consultant, []))
            members = Person.objects.filter(identifier__in=new_members).order_by('title')
            committee.members.set(members, bulk=True, clear=True)
            new_scientists = set(predicates.get(_project_scientist, []))
            scientists = Person.objects.filter(identifier__in=new_scientists).order_by('title')
            committee.project_scientists.set(scientists, bulk=True, clear=True)
            new_officers = set(predicates.get(_program_officer, []))
            officers = Person.objects.filter(identifier__in=new_officers).order_by('title')
            committee.program_officers.set(officers, bulk=True, clear=True)
            try:
                committee.save()
            except ValidationError:
                _logger.exception('Cannot save committee %s but pressing on', uri)

        # Nothing to report
        return set(), set(), set()


class CommitteeIndex(KnowledgeFolder):
    '''A committee index contains committees.'''
    subpage_types = ['edrncollabgroups.Committee']
    template = 'eke.knowledge/committee-index.html'

    def get_context(self, request: HttpRequest, *args, **kwargs) -> dict:
        context = super().get_context(request, *args, **kwargs)
        cbs = Page.objects.child_of(self).live().filter(title__endswith='Cancers Research Group').order_by(Lower('title'))
        others = Page.objects.child_of(self).live().exclude(title__endswith='Cancers Research Group').order_by(Lower('title'))
        context['collaborative_groups'], context['other_groups'] = cbs, others
        return context

    class RDFMeta:
        ingestor = Ingestor
