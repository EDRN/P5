# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: publications associated with protocols.'''

from django.core.management.base import BaseCommand
from sortedcontainers import SortedList
from eke.knowledge.models import Publication
from urllib.parse import urlparse
import rdflib, logging, dataclasses, csv


@dataclasses.dataclass(order=True)
class Protocol:
    dmcc_code: str
    title: str
    publications: set[object] = dataclasses.field(default_factory=set, init=True, compare=False)
    def __hash__(self):
        return hash(self.name)
    def write(self, writer):
        pubs = ', '.join([f'"{i.title}" ({i.pubMedID})' for i in self.publications])
        writer.writerow([self.dmcc_code, self.title, pubs])


class Command(BaseCommand):
    help = 'Make a CSV showing each protocol and all the publications associated with it'

    _protocol_rdf = 'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/protocols/@@rdf'
    _publication_predicate = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#publications')
    _protocol_type = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/types.rdf#Protocol')

    def add_arguments(self, parser):
        # parser.add_argument('--delay', default=3.0, type=float, help="Seconds to wait 'txit retreivals [%(default)f]")
        pass

    def read_rdf(self, url) -> dict:
        graph = rdflib.Graph()
        statements = {}
        graph.parse(url)
        for s, p, o in graph:
            predicates = statements.get(s, {})
            objects = predicates.get(p, SortedList())
            objects.add(o)
            predicates[p] = objects
            statements[s] = predicates
        return statements

    def _dmcc_code(self, uri) -> str:
        return urlparse(uri).path.split('/')[-1]

    def handle(self, *args, **options):
        verbosity = int(options['verbosity'])
        root_logger = logging.getLogger('')
        if verbosity >= 3:
            root_logger.setLevel(logging.DEBUG)

        protocols, statements = {}, self.read_rdf(self._protocol_rdf)
        for subject, predicates in statements.items():
            kind = predicates.get(rdflib.RDF.type, [''])[0]
            if kind != self._protocol_type: continue
            dmcc_code = self._dmcc_code(subject)
            title = str(predicates.get(rdflib.DCTERMS.title, ['«unknown»'])[0])
            pubs_uris = [str(i) for i in predicates.get(self._publication_predicate, [])]
            pubs = set([i for i in Publication.objects.filter(subject_uris__identifier__in=pubs_uris)])
            protocols[dmcc_code] = Protocol(dmcc_code=dmcc_code, title=title, publications=pubs)

        with open('protocols.csv', 'w', newline='') as io:
            writer = csv.writer(io)
            writer.writerow(['DMCC Code', 'Protocol Title', 'Publications'])
            for protocol in protocols.values():
                protocol.write(writer)
