# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: utilities.'''

from .knowledge import KnowledgeFolder, KnowledgeObject
from django.contrib.auth.models import User
from wagtail.models import Page, PageViewRestriction
from wagtail.query import PageQuerySet
from sortedcontainers import SortedList
import importlib, logging, rdflib, datetime, typing

_logger = logging.getLogger(__name__)


def filter_by_user(qs: PageQuerySet, user: User) -> PageQuerySet:
    '''Filter the pages in the query set ``qs`` by what the ``user`` can actually view.'''
    if not user.is_authenticated:
        qs = qs.public()
    elif not user.is_superuser:
        disallowed = PageViewRestriction.objects.exclude(groups__id=user.groups.all()).values_list("page", flat=True)
        qs = qs.exclude(id__in=disallowed)
    return qs


def aware_now():
    '''Return the current time in UTC as a non-naive (aware) time with the UTC time zone.'''
    return datetime.datetime.now(datetime.timezone.utc)


def get_class(name: str) -> type:
    '''Given the fully qualified ``name`` of a class, return that class.'''
    parts = name.split('.')
    moduleName = '.'.join(parts[:-1])
    module = importlib.import_module(moduleName)
    return getattr(module, parts[-1])


def edrn_schema_uri(element: str) -> str:
    '''Given an ``element`` name return the full schema URI used as an RDF predicate in EDRN.'''
    return 'http://edrn.nci.nih.gov/rdf/schema.rdf#' + element


class Ingestor(object):
    '''Base ingestor of RDF statements to populate site objects.

    This ingestor does the heavy lifting of parsing RDF, determining how to map the statements made therein
    to Wagtail/Django models, and set their various fields.
    '''
    def __init__(self, folder: KnowledgeFolder):
        if not isinstance(folder, KnowledgeFolder):
            raise ValueError(f'Ingestor expects a KnowledgeFolder, got {folder.__class__.__name__}')
        self.folder = folder

    def readRDF(self) -> dict:
        '''Read all the RDF sources of our folder and return the statements

        The statements are a dictionary of subject URI to a dictionary of predicate URI to a sorted list
        of objects (not objects in the OO sense, but in the language/semantic sense).
        '''
        graph = rdflib.Graph()
        self.statements = {}
        sources = self.folder.rdf_sources.all().filter(active=True)
        if len(sources) == 0:
            _logger.warn('For folder %r none of my RDF sources are active', self.folder)
        for source in sources:
            graph.parse(source.url)
        for s, p, o in graph:
            predicates = self.statements.get(s, {})
            objects = predicates.get(p, SortedList())
            objects.add(o)
            predicates[p] = objects
            self.statements[s] = predicates
        return self.statements

    def filter_by_rdf_type(self, statements: dict, type_uri: rdflib.URIRef) -> typing.Iterator[tuple]:
        '''Filter statements based on an RDF type URI.

        Out of the given ``statements``, yield only those subject URIs and matching predicates that
        describe objects with the given ``type_uri``.
        '''
        for subject_uri, predicates in statements.items():
            found_type = predicates.get(rdflib.RDF.type, [None])[0]
            if found_type == type_uri:
                yield subject_uri, predicates

    def getClass(self, uri: str, predicates: dict) -> type:
        '''From the given ``predicates`` describing a single object identified by ``uri``, return the
        class of that object. If the class is unknown, return ``None``.
        '''
        if rdflib.RDF.type not in predicates:
            _logger.info('Subject URI %s has no RDF type predicate', uri)
            return None
        typeURI = str(predicates[rdflib.RDF.type][0])
        types = self.folder.specific_deferred.RDFMeta.types
        cls = types.get(typeURI)
        if cls is None:
            _logger.debug(
                "Subject URI %s has type %s that isn't supported by container %s; expected 1 of {%s}",
                uri, typeURI, self.folder, ', '.join(types.keys())
            )
        return cls

    def getSlug(self, uri: rdflib.URIRef, predicates: dict) -> str:
        '''From the given ``predicates`` descibing a single object, figure out a good slug for it. By default,
        we return ``None`` which lets Wagtail figure out the right slug. Subclasses can override this and make
        a custom slug if needed.
        '''
        return None

    def getTitle(self, uri: rdflib.URIRef, predicates: dict) -> str:
        '''From the given ``predicates`` describing a single object, return the title of the object. By default,
        we look for the Dublin Core title. If we can't figure it out, return None. Subclasses can override this
        if needed. The object's subject ``uri`` is there too if you need.
        '''
        titles = [str(i) for i in predicates.get(rdflib.DCTERMS.title, [])]
        if len(titles) == 0: return None
        # 🔮 TOOD: Cutting off at 255 characters is necessary but also arbitrary. Is there a better word-
        # breaking algorithm we can use?
        return titles[0][:255]

    def getLive(self, predicates: dict) -> bool:
        '''From the given ``predicates`` describing a single object, return if this object should be live on the
        site. By default, we just return True. Subclasses can override this.
    '   '''
        return True

    def setAttributes(self, obj: Page, predicates: dict) -> bool:
        '''Set the attributes of ``obj`` using the values in ``predicates``. Return True if any updates are made,
        otherwise return False.
        '''
        modified = False
        for predicateURI, values in predicates.items():
            predicateURI = str(predicateURI)
            try:
                # Get RDF metadata from the narrowed Wagtail model
                rdfAttribute = obj.specific.RDFMeta.fields.get(predicateURI)
            except AttributeError:
                # Nope, it's a plain Django model
                rdfAttribute = obj.RDFMeta.fields.get(predicateURI)
            if rdfAttribute is None: continue
            try:
                # Get the field from the narrowed Wagtail model
                modelField = obj.specific._meta.get_field(rdfAttribute.name)
            except AttributeError:
                # Nope, get the field from a plain Django model
                modelField = obj._meta.get_field(rdfAttribute.name)
            fieldModified = rdfAttribute.modify_field(obj, values, modelField, predicates)
            if fieldModified: modified = True
        return modified

    def createObjects(self, uris: set, statements: dict) -> set:
        '''Create new objects in our container.

        This method creates new objects in our index (container, folder, whatever) identified by the RDF
        subject ``uris`` and sets their various attributes made in the ``statements``. A set of changed
        objects is returned.
        '''
        createdObjects = set()
        unknownObjectCount = 0
        for uri in uris:
            try:
                predicates = statements[rdflib.URIRef(uri)]
            except KeyError:
                # RDF "b node"
                continue
            cls = self.getClass(uri, predicates)
            if cls is None: continue
            slug, title, live = self.getSlug(uri, predicates), self.getTitle(uri, predicates), self.getLive(predicates)
            if title is None:
                unknownObjectCount += 1
                title = f'Unknown Object {unknownObjectCount}'
            instance = cls(title=title, draft_title=title, seo_title=title, slug=slug, live=live, identifier=uri)
            self.folder.specific_deferred.add_child(instance=instance)
            self.setAttributes(instance, predicates)
            instance.save()
            createdObjects.add(instance)
        return createdObjects

    def updateObjects(self, uris: set, statements: dict) -> set:
        '''Update objects in our folder.

        This method finds the objects that are descendents of the index (container, folder, whatever) that
        match the given ``uris`` and uses the ``statements`` made about them to update them. The objects already
        exist. Return a set of only those objects that have changed.
        '''
        updatedObjects = set()
        for uri in uris:
            obj = KnowledgeObject.objects.child_of(self.folder).filter(identifier=uri).first()
            if not obj:
                _logger.warning("Container %r should have knowledge obj %s but it's not here", self.folder, uri)
                continue
            try:
                # Narrow the Wagtail model
                obj = obj.specific
            except AttributeError:
                # It was a plain Django model all along
                pass
            if self.setAttributes(obj, statements[rdflib.URIRef(uri)]):
                obj.save()
                updatedObjects.add(obj)
        return updatedObjects

    def ingest(self):
        '''Ingest data from RDF sources and populate/update objects in the site.

        Subclasses typically will augment rather than override this method. But we also follow the
        template method design pattern, so the steps performed by this method may in turn be overridden
        and/or augmented.
        '''
        _logger.debug('Starting ingest for %s', self.folder)
        if not self.folder.ingest:
            _logger.info('Ingest disabled for %r, skipping it', self.folder)
        statements = self.readRDF()
        existingURIs = set([i.identifier for i in KnowledgeObject.objects.child_of(self.folder)])
        statementURIs = set([str(i) for i in statements.keys()])
        newURIs = statementURIs - existingURIs
        deadURIs = existingURIs - statementURIs
        updateURIs = statementURIs & existingURIs
        _logger.debug('Ingest new=%d, updating=%d, dead objects=%d', len(newURIs), len(updateURIs), len(deadURIs))
        newObjects = self.createObjects(newURIs, statements)
        updatedObjects = self.updateObjects(updateURIs, statements)
        KnowledgeObject.objects.child_of(self.folder).filter(identifier__in=deadURIs).delete()
        self.folder.refresh_from_db()
        return newObjects, updatedObjects, deadURIs
