# encoding: utf-8


import rdflib

_piURI   = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#pi')
_coPIURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#copi')
_coIURI  = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#coi')
_iURI    = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#investigator')
_empURI  = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#employmentActive')


def readRDF(url):
    graph = rdflib.Graph()
    graph.parse(url)
    statements = {}
    for s, p, o in graph:
        if s not in statements:
            statements[s] = {}
        predicates = statements[s]
        if p not in predicates:
            predicates[p] = []
        predicates[p].append(o)
    return statements


def log(message, site, kind, person):
    site, kind, person = site.split(u'/')[-1], kind.split(u'#')[-1], person.split(u'/')[-1]
    print u'{}: site {}, type {}, person {}'.format(message, site, kind, person)


def main():
    people = readRDF('file:/tmp/people.rdf')
    sites = readRDF('file:/tmp/sites.rdf')
    for siteURI, sitePredicates in sites.items():
        for predicate in (_piURI, _coPIURI, _coIURI, _iURI):
            members = sitePredicates.get(predicate, [])
            for member in members:
                person = people.get(member)
                if person is None:
                    log(u'Person mentioned in site not found', siteURI, predicate, member)
                status = person.get(_empURI)
                if status is not None and len(status) > 0 and unicode(status[0]) == u'Former employee':
                    log(u'Former person still has coveted role in site', siteURI, predicate, member)


if __name__ == '__main__':
    main()
