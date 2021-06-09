# encoding: utf-8


import rdflib, urlparse, csv, cStringIO, codecs


_cancerTypePredicateURI = rdflib.term.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#cancerType')
_protocolTypeURI = rdflib.term.URIRef(u'http://edrn.nci.nih.gov/rdf/types.rdf#Protocol')
_diseaseTypeURI = rdflib.term.URIRef(u'http://edrn.nci.nih.gov/rdf/types.rdf#Disease')


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def _dmccID(uri):
    u'''Return the DMCC identification number from an RDF subject URI'''
    return urlparse.urlparse(uri).path.split('/')[-1]


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
    statements = _readRDF(u'file:new-diseases.rdf')
    diseases = {}
    for s, p in statements.items():
        kind = p.get(rdflib.RDF.type)
        if kind[0] != _diseaseTypeURI: continue
        title = p.get(rdflib.namespace.DCTERMS.title, [u'«unknown disease»'])
        diseases[_dmccID(s)] = unicode(title[0])

    statements = _readRDF(u'file:new-protocols.rdf')
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

    counts = {}
    for protocolID, cancerTypes in protocols.items():
        for cancerType in cancerTypes:
            if cancerType not in diseases:
                print '%s (protocol) has unknown cancer type %s (disease)' % (protocolID, cancerType)
            count = counts.get(diseases[cancerType], 0)
            count += 1
            counts[diseases[cancerType]] = count

    with open('cancerTypes.csv', 'wb') as f:
        wr = UnicodeWriter(f)
        wr.writerow(['Cancer Type', 'Count'])
        for cancerType, count in counts.items():
            wr.writerow([cancerType, unicode(count)])


if __name__ == '__main__':
    main()