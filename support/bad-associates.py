# encoding: utf-8
#
# Show sites with bad member types

import rdflib, urlparse


_memberTypeURI = rdflib.term.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#memberType')


def _readRDF(url):
    u'''Read the RDF statements and return s/p/o dict'''
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


def main():
    statements = _readRDF(u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/sites/@@rdf')
    badSites = []
    for s, p in statements.items():
        memberType = p.get(_memberTypeURI, None)
        if memberType and memberType[0].startswith(u'Assocaite'):
            path = urlparse.urlparse(s).path
            badSites.append(int(path.split(u'/')[-1]))
    badSites.sort()
    print(u', '.join([unicode(i) for i in badSites]))


if __name__ == '__main__':
    main()