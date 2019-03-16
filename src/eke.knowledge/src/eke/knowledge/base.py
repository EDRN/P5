# encoding: utf-8

u'''Abstract (or not)) base classes for EKE'''


from . import _
from .dublincore import TITLE_URI
from .errors import IngestDisabled, IngestError, RDFTypeMismatchError, TitlePredicateMissingError
from .interfaces import IIngestor
from .knowledgefolder import IKnowledgeFolder
from .knowledgeobject import IKnowledgeObject
from .utils import IngestConsequences, publish, setValue
from Acquisition import aq_inner
from five import grok
from plone.dexterity.utils import createContentInContainer
from z3c.relationfield import RelationValue
from zope import schema
from zope.component import getUtility
from zope.intid.interfaces import IIntIds
from zope.interface import Invalid
import rdflib, plone.api, logging


DC_TITLE = rdflib.URIRef(TITLE_URI)

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
    def getObjID(self, subjectURI, titles, predicates):
        u'''Return a custom object ID to use or None if we should just let a behavior like
        name-from-title do it for us. Subclasses may override this.'''
        return None
    def _checkPredicates(self, subjectURI, predicates):
        u'''Check the given ``predicates`` to see if they're appropriate for the interfaces of the objects
        to be created. If so, return the type's interface, the FTI, the predicate map, and the object's title,
        and a possible object ID for it to use.  If not, raise an error.'''
        iface = self.getInterfaceForContainedObjects()
        fti = iface.getTaggedValue('fti')
        predicateMap = iface.getTaggedValue('predicates')
        neededTypeURI = rdflib.URIRef(iface.getTaggedValue('typeURI'))
        typeURI, titles = predicates[rdflib.RDF.term('type')][0], self.getTitles(predicates)
        objID = self.getObjID(subjectURI, titles, predicates)
        if typeURI != neededTypeURI: raise RDFTypeMismatchError(neededTypeURI, typeURI)
        if not titles or not titles[0]: raise TitlePredicateMissingError(subjectURI)
        return iface, fti, predicateMap, unicode(titles[0]), objID
    def setValue(self, obj, fti, iface, predicate, predicateMap, values):
        u'''Look up the field of ``obj`` matching ``predicate`` in the ``predicateMap``` and set it to ``values```.
        Use the ``fti`` to warn of any issue and access fields via the ``iface``.'''
        setValue(obj, fti, iface, predicate, predicateMap, values)
    def createObjects(self, context, uris, statements):
        u'''Create objects in ``context`` identified by ``uris`` and described in the ``statements``.  Return
        sequence of those created objects. Subclasses may override this for special ingest needs.'''
        createdObjects = []
        for uri in uris:
            predicates = statements[uri]
            try:
                iface, fti, predicateMap, title, objID = self._checkPredicates(uri, predicates)
            except IngestError as ex:
                _logger.exception(u'Ingest error on %s: %r; skipping %s', u'/'.join(context.getPhysicalPath()), ex, uri)
                continue
            if objID is None:
                obj = createContentInContainer(context, fti, title=title, identifier=unicode(uri))
            else:
                obj = createContentInContainer(context, fti, id=objID, title=title, identifier=unicode(uri))
            for predicate in predicateMap:
                predicate = rdflib.URIRef(predicate)
                if predicate == DC_TITLE: continue  # Already set
                values = predicates.get(predicate)
                if not values: continue
                values = [i.toPython() for i in values]
                try:
                    self.setValue(obj, fti, iface, predicate, predicateMap, values)
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
            iface, fti, predicateMap, title, objID = self._checkPredicates(uri, predicates)
            for predicate, (fieldName, isReference) in predicateMap.iteritems():
                field = iface.get(fieldName)
                if field is None:
                    _logger.info('=== During update of %r field %s was not found, skipping', iface, fieldName)
                    continue
                fieldBinding = field.bind(obj)
                newVals = predicates.get(rdflib.URIRef(predicate), [])
                newVals = [i.toPython() for i in newVals]
                if isReference:
                    rvs = fieldBinding.get(obj)
                    if rvs is None: continue
                    if schema.interfaces.ICollection.providedBy(field):
                        paths = [i.to_path for i in rvs]
                    else:
                        paths = [rvs.to_path]
                    matches = catalog(path={'query': paths, 'depth': 0})
                    currentRefs = [i['identifier'].decode('utf-8') for i in matches]
                    currentRefs.sort()
                    newVals.sort()
                    if currentRefs != newVals:
                        self.setValue(obj, fti, iface, predicate, predicateMap, newVals)
                        objectUpdated = True
                else:
                    currentVals = fieldBinding.get(obj)
                    if schema.interfaces.ICollection.providedBy(field):
                        if currentVals != newVals and currentVals is not None:
                            self.setValue(obj, fti, iface, predicate, predicateMap, newVals)
                            objectUpdated = True
                    else:
                        if len(newVals) > 0:
                            if currentVals != newVals[0]:
                                # Note that site memberType may always be triggered here because
                                # the new value may be "Associate Member C2 - Former" whereas we
                                # truncate that in setValue to "Associate Member C". This just
                                # causes unneeded object updates but is otherwise harmless (if
                                # slow).
                                self.setValue(obj, fti, iface, predicate, predicateMap, newVals)
                                objectUpdated = True
            if objectUpdated:
                obj.reindexObject()
                updatedObjects.append(obj)
        return updatedObjects
    def readRDF(self, url):
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
        statements = {}
        for rdfDataSource in context.rdfDataSources:
            statements.update(self.readRDF(rdfDataSource))
        results = catalog(
            object_provides=IKnowledgeObject.__identifier__,
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
        return IngestConsequences(newObjects, updatedObjects, deadURIs, statements)
