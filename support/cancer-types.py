# encoding: utf-8


import rdflib, urllib, pprint


_cancerTypePredicateURI = rdflib.term.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#cancerType')
_protocolTypeURI = rdflib.term.URIRef('http://edrn.nci.nih.gov/rdf/types.rdf#Protocol')
_diseaseTypeURI = rdflib.term.URIRef('http://edrn.nci.nih.gov/rdf/types.rdf#Disease')


def _dmccID(uri):
    '''Return the DMCC identification number from an RDF subject URI'''
    rc = urllib.parse.urlparse(uri).path.split('/')[-1]
    return rc


def _readRDF(url):
    '''Read the RDF statements and return s/p/o dict'''
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
    # statements = _readRDF('https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/diseases/@@rdf')
    statements = _readRDF('file:/Users/kelly/Documents/Clients/JPL/Cancer/Portal/Development/P6/diseases.rdf')
    diseases = {}
    for s, p in statements.items():
        kind = p.get(rdflib.RDF.type)
        if kind[0] != _diseaseTypeURI: continue
        title = p.get(rdflib.namespace.DCTERMS.title, ['«unknown disease»'])
        diseases[_dmccID(s)] = str(title[0])

    # Note: this relies on the new CancerDataExpo that outputs RDF resources for cancerType
    # statements = _readRDF('https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/protocols/@@rdf')
    statements = _readRDF('file:/Users/kelly/Documents/Clients/JPL/Cancer/Portal/Development/P6/protocols.rdf')
    protocols = {}
    for s, p in statements.items():
        kind = p.get(rdflib.RDF.type)
        if kind[0] != _protocolTypeURI: continue
        protocolID = _dmccID(s)
        if protocolID not in protocols:
            protocols[protocolID] = []
        cancerTypes = p.get(_cancerTypePredicateURI, [])
        for cancerType in cancerTypes:
            diseaseID = _dmccID(cancerType)
            protocols[protocolID].append(diseaseID)

    for protocolID, cancerTypes in protocols.items():
        for cancerType in cancerTypes:
            if cancerType not in diseases:
                print(f'{protocolID} (protocol) has unknown cancer type {cancerType}')

    pprint.pprint(protocols)


if __name__ == '__main__':
    main()
