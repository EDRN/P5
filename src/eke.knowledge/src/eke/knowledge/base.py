# encoding: utf-8

u'''Abstract (or not)) base classes for EKE'''


from . import _
from .errors import IngestDisabled, IngestError, RDFTypeMismatchError, TitlePredicateMissingError
from .interfaces import IIngestor
from .utils import IngestConsequences, publish
from .knowledgefolder import IKnowledgeFolder
from Acquisition import aq_inner
from five import grok
from plone.dexterity.utils import createContentInContainer
from plone.supermodel import model
from z3c.relationfield import RelationValue
from zope import schema
from zope.component import getUtility
from zope.intid.interfaces import IIntIds
import rdflib, plone.api, logging


DC_TITLE = rdflib.URIRef(u'http://purl.org/dc/terms/title')

_logger = logging.getLogger(__name__)


class Ingestor(grok.Adapter):
    grok.context(IKnowledgeFolder)
    grok.provides(IIngestor)
    def getInterfaceForContainedObjects(self):
        u'''Return the interface for objects contained'''
        raise NotImplementedError(u'Subclasses need to implement getInterfaceForContainedObjects')
    def getTitles(self, predicates):
        u'''Get the DC title from ``predicates``. Override this if you need'''
        return predicates.get(DC_TITLE)
    def _checkPredicates(self, predicates):
        u'''Check the given ``predicates`` to see if they're appropriate for the interfaces of the objects
        to be created. If so, return the type's interface, the FTI, the predicate map, and the object's title.
        If not, raise an error.'''
        iface = self.getInterfaceForContainedObjects()
        fti = iface.getTaggedValue('fti')
        predicateMap = iface.getTaggedValue('predicates')
        ndeededTypeURI = rdflib.URIRef(iface.getTaggedValue('typeURI'))
        typeURI, titles = predicates[rdflib.RDF.term('type')][0], self.getTitles(predicates)
        if typeURI != ndeededTypeURI: raise RDFTypeMismatchError(ndeededTypeURI, typeURI)
        if not titles or not titles[0]: raise TitlePredicateMissingError()
        return iface, fti, predicateMap, unicode(titles[0])
    def _setValue(self, obj, fti, iface, predicate, predicateMap, values):
        u'''Look up the field of ``obj`` matching ``predicate`` in the ``predicateMap``` and set it to ``values```.
        Use the ``fti`` to warn of any issue and access fields via the ``iface``.'''
        catalog = plone.api.portal.get_tool('portal_catalog')
        fieldName, isReference = predicateMap[unicode(predicate)]
        if not values:
            _logger.info(u'Type %s needs pred %s but not given; leaving %s un-set', fti, predicate, fieldName)
            return
        field = iface.get(fieldName)
        fieldBinding = field.bind(obj)
        if isReference:
            idUtil = getUtility(IIntIds)
            items = [i.getObject() for i in catalog(identifier=values)]
            if len(items) != len(values):
                _logger.info(
                    u'Type %s has reference predicate %s: linked to %d URIs, yet only %d found',
                    fti, predicate, len(values), len(items)
                )
            intids = [idUtil.getId(i) for i in items]
            rvs = [RelationValue(i) for i in intids]
            if schema.interfaces.ICollection.providedBy(field):
                fieldBinding.set(obj, rvs)
            elif len(items) > 0:
                fieldBinding.set(obj, rvs[0])
        else:  # Non-reference field
            if schema.interfaces.ICollection.providedBy(field):  # Multi-valued
                fieldBinding.validate(values)
                fieldBinding.set(obj, values)
            else:  # Scalar
                fieldBinding.validate(values[0])
                fieldBinding.set(obj, values[0])
    def createObjects(self, context, uris, statements):
        u'''Create objects in ``context`` identified by ``uris`` and described in the ``statements``.  Return
        sequence of those created objects. Subclasses may override this for special ingest needs.'''
        createdObjects = []
        for uri in uris:
            predicates = statements[uri]
            try:
                iface, fti, predicateMap, title = self._checkPredicates(predicates)
            except IngestError as ex:
                _logger.exception(u'Ingest error on %s: %r; skipping %s', u'/'.join(context.getPhysicalPath()), ex, uri)
                continue
            obj = createContentInContainer(context, fti, title=title, identifier=unicode(uri))
            for predicate in predicateMap:
                predicate = rdflib.URIRef(predicate)
                if predicate == DC_TITLE: continue  # Already set
                values = predicates.get(predicate)
                if not values: continue  # No values? Skip
                values = [i.toPython() for i in values]
                try:
                    self._setValue(obj, fti, iface, predicate, predicateMap, values)
                except schema.ValidationError:
                    _logger.exception(u'Data "%r" for field %s invalid—skipping', values, predicate)
                    continue
            publish(obj)
            obj.reindexObject()
            createdObjects.append(obj)
        return createdObjects
    def updateObjects(self, context, uris, brains, statements):
        u'''Update objects with matching ``uris`` in the ``context`` using ``statements``.'''
        catalog = plone.api.portal.get_tool('portal_catalog')
        updatedObjects = []
        for uri in uris:
            brain = brains[uri]
            obj = brain.getObject()
            predicates = statements[uri]
            objectUpdated = False
            iface, fti, predicateMap, title = self._checkPredicates(predicates)
            for predicate, (fieldName, isReference) in predicateMap.iteritems():
                field = iface.get(fieldName)
                fieldBinding = field.bind(obj)
                newVals = predicates.get(rdflib.URIRef(predicate), [])
                newVals = [i.toPython() for i in newVals]
                if isReference:
                    rvs = fieldBinding.get(obj)
                    paths = [i.to_path for i in rvs]
                    matches = catalog(path={'query': paths, 'depth': 0})
                    currentRefs = [i['identifier'].decode('utf-8') for i in matches]
                    currentRefs.sort()
                    newVals.sort()
                    if currentRefs != newVals:
                        self._setValue(obj, fti, iface, predicate, predicateMap, newVals)
                        objectUpdated = True
                else:
                    currentVals = fieldBinding.get(obj)
                    if schema.interfaces.ICollection.providedBy(field):
                        if currentVals != newVals:
                            self._setValue(obj, fti, iface, predicate, predicateMap, newVals)
                            objectUpdated = True
                    else:
                        if len(newVals) > 0:
                            if currentVals != newVals[0]:
                                self._setValue(obj, fti, iface, predicate, predicateMap, newVals)
                                objectUpdated = True
            if objectUpdated:
                obj.reindexObject()
                updatedObjects.append(obj)
        return updatedObjects
    def _readRDF(self, url):
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
    def ingest(self):
        u'''Ingest that RDF data'''
        context = aq_inner(self.context)
        if not context.ingestEnabled: raise IngestDisabled(context)
        catalog = plone.api.portal.get_tool('portal_catalog')
        statements = self._readRDF(context.rdfDataSource)
        results = catalog(
            object_provides=IKnowledgeFolder.__identifier__,
            path=dict(query='/'.join(context.getPhysicalPath()), depth=1)
        )
        existingBrains = {}
        for i in results:
            uri = i['identifier'].decode('utf-8')
            existingBrains[rdflib.URIRef(uri)] = i
        existingURIs = set(existingBrains.keys())
        statementURIs = set(statements.keys())
        newURIs = statementURIs - existingURIs
        deadURIs = existingURIs - statementURIs
        updateURIs = statementURIs & existingURIs
        newObjects = self.createObjects(context, newURIs, statements)
        updatedObjects = self.updateObjects(context, updateURIs, existingBrains, statements)
        context.manage_delObjects([existingBrains[i]['id'].decode('utf-8') for i in deadURIs])
        return IngestConsequences(newObjects, updatedObjects, deadURIs)
