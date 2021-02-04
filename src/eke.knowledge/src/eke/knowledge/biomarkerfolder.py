# encoding: utf-8

u'''Biomarker folder'''

from . import _
from .base import Ingestor
from .biomarker import IBiomarker, IBiomarkerBodySystem, IBodySystemStudy, IStudyStatistics, updatePhases
from .biomarkerpanel import IBiomarkerPanel
from .bodysystem import IBodySystem
from .elementalbiomarker import IElementalBiomarker
from .knowledgefolder import IKnowledgeFolder
from .protocol import IProtocol
from .utils import IngestConsequences, publish
from Acquisition import aq_inner
from plone.dexterity.utils import createContentInContainer
from plone.i18n.normalizer.interfaces import IIDNormalizer
from Products.Five import BrowserView
from z3c.relationfield import RelationValue
from zope import schema
from zope.component import getUtility, getMultiAdapter
from zope.event import notify
from zope.interface import implementer
from zope.intid.interfaces import IIntIds
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary
import logging, plone.api, rdflib, uuid, contextlib, urllib2, transaction

_logger = logging.getLogger(__name__)

# Specific URIs
_accessPredicateURI                      = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#AccessGrantedTo')
_biomarkerPredicateURI                   = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Biomarker')
_bmOrganDataTypeURI                      = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#BiomarkerOrganData')
_bmTitlePredicateURI                     = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Title')
_certificationPredicateURI               = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#certification')
_hasBiomarkerOrganStudyDatasPredicateURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#hasBiomarkerOrganStudyDatas')
_hasBiomarkerStudyDatasPredicateURI      = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#hasBiomarkerStudyDatas')
_hgncPredicateURI                        = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#HgncName')
_isPanelPredicateURI                     = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#IsPanel')
_memberOfPanelPredicateURI               = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#memberOfPanel')
_organPredicateURI                       = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Organ')
_referencesStudyPredicateURI             = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#referencesStudy')
_sensitivityDatasPredicateURI            = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#SensitivityDatas')

# Certification URIs
_cliaCertificationURI = rdflib.URIRef(u'http://www.cms.gov/Regulations-and-Guidance/Legislation/CLIA/index.html')
_fdaCeritificationURI = rdflib.URIRef(u'http://www.fda.gov/regulatoryinformation/guidances/ucm125335.htm')

# Other URIs
predicateURIBase     = u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#'

# Map from RDF predicate URI to (field name, boolean true if reference field)
_biomarkerPredicates = {
    # For biomarkers and other related objects
    unicode(_hgncPredicateURI): ('hgncName', False),
    predicateURIBase + u'Description': ('description', False),
    predicateURIBase + u'QAState': ('qaState', False),
    predicateURIBase + u'Phase': ('phase', False),
    predicateURIBase + u'referencesStudy': ('protocols', True),  # FIXME? What about BodySystemStudy's singular "protocol" field?
    predicateURIBase + u'referencedInPublication': ('publications', True),
    predicateURIBase + u'referencesResource': ('resources', True),
    predicateURIBase + u'AssociatedDataset': ('datasets', True),
    predicateURIBase + u'ShortName': ('shortName', False),
    predicateURIBase + u'Alias': ('bmAliases', False),
    predicateURIBase + u'PerformanceComment': ('performanceComment', False),
    predicateURIBase + u'Type': ('biomarkerType', False),
    predicateURIBase + u'AssociatedDataset': ('datasets', True),

    # For biomarker-body-systems
    predicateURIBase + u'PerformanceComment': ('performanceComment', False),

    # For body-system-studies
    predicateURIBase + u'DecisionRule': ('decisionRule', False),

    # For study-stats
    predicateURIBase + u'Sensitivity': ('sensitivity', False),
    predicateURIBase + u'Specificity': ('specificity', False),
    predicateURIBase + u'NPV': ('npv', False),
    predicateURIBase + u'PPV': ('ppv', False),
    predicateURIBase + u'Prevalence': ('prevalence', False),
    predicateURIBase + u'SensSpecDetail': ('details', False),
    predicateURIBase + u'SpecificAssayType': ('specificAssayType', False),
}

_organNameToCollaborativeGroupName = {
    u'Breast': u'Breast and Gynecologic Cancers Research Group',
    u'Ovary': u'Breast and Gynecologic Cancers Research Group',
    u'Colon': u'G.I. and Other Associated Cancers Research Group',
    u'Esophagus': u'G.I. and Other Associated Cancers Research Group',
    u'Liver': u'G.I. and Other Associated Cancers Research Group',
    u'Pancreas': u'G.I. and Other Associated Cancers Research Group',
    u'Lung': u'Lung and Upper Aerodigestive Cancers Research Group',
    u'Prostate': u'Prostate and Urologic Cancers Research Group',
    u'Bladder': u'Prostate and Urologic Cancers Research Group',
    u'Head & neck, NOS': u'Lung and Upper Aerodigestive Cancers Research Group',
    # Used only in testing:
    u'Rectum': u'G.I. and Other Associated Cancers Research Group'
}

_defaultPrivateBiomarkerAdmonition = u'''
Organ-specific information for this biomarker is currently being annotated or is "under review".
Logging in may give you privileges to view additional information.
Contact the
<a href='mailto:ic-portal@jpl.nasa.gov'>Informatics Center</a>
if you believe you should have access to this biomarker.
'''


def flatten(l):
    u'''Flatten a list.'''
    for i in l:
        if isinstance(i, list):
            for j in flatten(i):
                yield j
        else:
            yield i


class IBiomarkerFolder(IKnowledgeFolder):
    u'''Biomarker folder.'''
    bmoDataSource = schema.TextLine(
        title=_(u'Biomarker-Organ RDF Data Source'),
        description=_(u'URL to a source of RDF data that supplements the RDF data source with biomarker-organ data.'),
        required=True
    )
    bmuDataSource = schema.TextLine(
        title=_(u'Biomarker-BioMuta RDF Data Source'),
        description=_(u'URL to a source of RDF data that supplements the RDF data source with biomarker-biomuta data.'),
        required=True
    )
    idDataSource = schema.TextLine(
        title=_(u'Biomarker ID External Resource API Link'),
        description=_(u'URL to a api that allows querying biomarker ids for links and alternative ids of external resources.'),
        required=True
    )
    bmSumDataSource = schema.TextLine(
        title=_(u'Summary Data URL'),
        description=_(u'URL to summary data in JSON format for biomarkers.'),
        required=False,
    )
    dataSummary = schema.TextLine(
        title=_(u'Biomarker Statistics'),
        description=_(u'Data for biomarker statistical graphics.'),
        required=False
    )
    disclaimer = schema.Text(
        title=_(u'Disclaimer'),
        description=_(u'Legal disclaimer to display on Biomarker Folder pages.'),
        required=False,
    )
    privateBiomarkerAdmonition = schema.Text(
        title=_(u'Private Biomarker Admonition'),
        description=_(u'Message to display for biomarkers that are not yet public.'),
        required=True,
        default=_defaultPrivateBiomarkerAdmonition
    )


class BiomarkerIngestor(Ingestor):
    def getInterfaceForContainedObjects(self, predicates):
        raise NotImplementedError(u'{} handles its ingest specially'.format(self.__class__.__name__))
    def updateBiomarker(self, biomarkerObj, fti, iface, predicates, context, biomarkerStatements, request):
        # Set biomarker fields; TODO: REFACTOR HERE?
        for predicate, (fieldName, isReference) in _biomarkerPredicates.iteritems():
            values = predicates.get(rdflib.URIRef(predicate))
            if not values: continue
            values = [i.toPython() for i in values]
            try:
                self.setValue(biomarkerObj, fti, iface, predicate, _biomarkerPredicates, values)
            except schema.ValidationError:
                _logger.exception(u'RDF data "%r" for biomarker field "%s" invalid; skipping', values, predicate)
                continue
        # Set access
        if _accessPredicateURI in predicates:
            groupIDs = [unicode(i) for i in predicates[_accessPredicateURI]]
            biomarkerObj.accessGroups = groupIDs
            settings = [dict(type='group', roles=[u'Reader'], id=i) for i in groupIDs]
            sharing = getMultiAdapter((biomarkerObj, request), name=u'sharing')
            sharing.update_role_settings(settings)
        # Add biomarker-study-data
        protocolRVs = []
        if _hasBiomarkerStudyDatasPredicateURI in predicates:
            catalog = plone.api.portal.get_tool('portal_catalog')
            idUtil = getUtility(IIntIds)
            bag = biomarkerStatements[predicates[_hasBiomarkerStudyDatasPredicateURI][0]]
            for subjectURI, objects in bag.iteritems():
                if subjectURI == rdflib.RDF.term('type'): continue
                # Assume anything else is a list item pointing to BiomarkerStudyData objects
                for bmsd in [biomarkerStatements[i] for i in objects]:
                    # Right now, we use just the "referencesStudy" predicate, if it's present
                    if _referencesStudyPredicateURI not in bmsd: continue
                    protocols = [p.getObject() for p in catalog(identifier=unicode(bmsd[_referencesStudyPredicateURI][0]))]
                    protocolRVs.extend([RelationValue(idUtil.getId(p)) for p in protocols])
                    for protocol in protocols:
                        self._addBiomarkerToProtocol(biomarkerObj, protocol)
            biomarkerObj.protocols = protocolRVs
            notify(ObjectModifiedEvent(biomarkerObj))
    def addStatistics(self, bodySystemStudy, bags, statements):
        # Gather all the URIs
        sensitivityURIs = []
        for bag in bags:
            preds = statements[bag]
            del preds[rdflib.RDF.term('type')]
            sensitivityURIs.extend(flatten(preds.values()))
        # For each set of statistics...
        for sensitivityURI in sensitivityURIs:
            predicates = statements[sensitivityURI]
            stats = createContentInContainer(
                bodySystemStudy,
                'eke.knowledge.studystatistics',
                id=unicode(uuid.uuid1().hex),
                title=sensitivityURI
            )
            # TODO: refactor here
            for predicate, (fieldName, isReference) in _biomarkerPredicates.iteritems():
                values = predicates.get(rdflib.URIRef(predicate))
                if not values: continue
                values = [i.toPython() for i in values]
                try:
                    self.setValue(stats, 'eke.knowledge.studystatistics',
                        IStudyStatistics, predicate, _biomarkerPredicates, values)
                except schema.ValidationError:
                    _logger.exception(u'RDF data "%r" for studystatistics field "%s" invalid; skipping', values, predicate)
                    continue
    def addStudiesToOrgan(self, biomarkerBodySystem, bags, statements):
        catalog = plone.api.portal.get_tool('portal_catalog')
        normalize = getUtility(IIDNormalizer).normalize
        idUtil = getUtility(IIntIds)
        bmStudyDataURIs = []
        # The RDF may contain an empty <hasBiomarkerStudyDatas/>, which means that
        # there will be just an empty Literal '' in the bags list (which will be a
        # one item list). In that case, don't bother adding studies.
        if len(bags) == 1 and unicode(bags[0]) == u'': return
        for bag in bags:
            preds = statements[bag]
            del preds[rdflib.RDF.term('type')]
            bmStudyDataURIs.extend(flatten(preds.values()))
        for studyURI in bmStudyDataURIs:
            bmStudyDataPredicates = statements[studyURI]
            if _referencesStudyPredicateURI not in bmStudyDataPredicates: continue
            results = catalog(identifier=[unicode(i) for i in bmStudyDataPredicates[_referencesStudyPredicateURI]])
            protocols = [i.getObject() for i in results]
            if len(protocols) < 1:
                _logger.warn(
                    u'Protocol "%s" not found for biomarker body system "%r"',
                    bmStudyDataPredicates[_referencesStudyPredicateURI][0],
                    biomarkerBodySystem.identifier
                )
                continue
            identifier = unicode(protocols[0].identifier.split(u'/')[-1]) + u'-' + unicode(normalize(protocols[0].title))
            bodySystemStudy = None
            if identifier not in biomarkerBodySystem.keys():
                bodySystemStudy = createContentInContainer(
                    biomarkerBodySystem,
                    'eke.knowledge.bodysystemstudy',
                    title=protocols[0].title,
                    description=protocols[0].description,
                    identifier=unicode(identifier)
                )
            else:
                bodySystemStudy = biomarkerBodySystem[identifier]
            # TODO: REFACTOR HERE?
            for predicate, (fieldName, isReference) in _biomarkerPredicates.iteritems():
                values = bmStudyDataPredicates.get(rdflib.URIRef(predicate))
                if not values: continue
                values = [i.toPython() for i in values]
                try:
                    self.setValue(bodySystemStudy, 'eke.knowledge.bodysystemstudy',
                        IBodySystemStudy, predicate, _biomarkerPredicates, values)
                except schema.ValidationError:
                    _logger.exception(u'RDF data "%r" for bodysystemstudy field "%s" invalid; skipping', values, predicate)
                    continue
            bodySystemStudy.protocol = RelationValue(idUtil.getId(protocols[0]))
            notify(ObjectModifiedEvent(bodySystemStudy))
            self._addBiomarkerToProtocol(bodySystemStudy.aq_parent.aq_parent, protocols[0])
            if _sensitivityDatasPredicateURI in bmStudyDataPredicates:
                bags = bmStudyDataPredicates[_sensitivityDatasPredicateURI]
                self.addStatistics(bodySystemStudy, bags, statements)
    def addOrganSpecificInformation(self, biomarkers, statements):
        # biomarkers dict of uri to biomarker obj
        # statements = biomarker-organ statements s/p/o
        catalog, idUtil = plone.api.portal.get_tool('portal_catalog'), getUtility(IIntIds)
        for uri, predicates in statements.iteritems():
            try:
                if predicates[rdflib.RDF.term('type')][0] != _bmOrganDataTypeURI: continue
                biomarker = biomarkers[predicates[_biomarkerPredicateURI][0]]
            except KeyError:
                # No type or matching biomarker, skip it
                continue
            organName = unicode(predicates[_organPredicateURI][0])
            results = catalog(Title=organName, object_provides=IBodySystem.__identifier__)  # *Must* be capital Title
            if len(results) < 1:
                _logger.warn(u'Unknown organ %s for biomarker %s; skipping organ-specifics', organName, biomarker.title)
                continue
            biomarkerBodySystem = createContentInContainer(
                biomarker,
                'eke.knowledge.biomarkerbodysystem',
                identifier=unicode(uri),
                title=organName,
                bodySystem=RelationValue(idUtil.getId(results[0].getObject()))
            )
            # TODO: REFACTOR HERE?
            for predicate, (fieldName, isReference) in _biomarkerPredicates.iteritems():
                values = predicates.get(rdflib.URIRef(predicate))
                if not values: continue
                values = [i.toPython() for i in values]
                try:
                    self.setValue(biomarkerBodySystem, 'eke.knowledge.biomarkerbodysystem',
                        IBiomarkerBodySystem, predicate, _biomarkerPredicates, values)
                except schema.ValidationError:
                    _logger.exception(u'RDF data "%r" for biomarker field "%s" invalid; skipping', values, predicate)
                    continue
            # Make a note of the collaborative group based on the organ
            collaborativeGroupName = _organNameToCollaborativeGroupName.get(organName)
            if collaborativeGroupName:
                currentGroups = biomarker.collaborativeGroup if biomarker.collaborativeGroup else []
                if collaborativeGroupName not in currentGroups:
                    currentGroups.append(collaborativeGroupName)
                    biomarker.collaborativeGroup = currentGroups
            if _hasBiomarkerOrganStudyDatasPredicateURI in predicates:
                bags = predicates[_hasBiomarkerOrganStudyDatasPredicateURI]
                self.addStudiesToOrgan(biomarkerBodySystem, bags, statements)
            certificationURIs = predicates.get(_certificationPredicateURI, [])
            for certificationURI in certificationURIs:
                if certificationURI == _cliaCertificationURI:
                    biomarkerBodySystem.cliaCertification = True
                elif certificationURI == _fdaCeritificationURI:
                    biomarkerBodySystem.fdaCertification = True
    def getSummaryData(self, source):
        # This could be refactored with several other *folder.py files
        with contextlib.closing(urllib2.urlopen(source)) as bytestring:
            return bytestring.read()
    def _addBiomarkerToProtocol(self, biomarker, protocol):
        if protocol.biomarkers is None: protocol.biomarkers = []
        currentIDs = [i.to_id for i in protocol.biomarkers]
        biomarkerID = getUtility(IIntIds).getId(biomarker)
        if biomarkerID not in currentIDs:
            protocol.biomarkers.append(RelationValue(biomarkerID))
    def _removeProtocolToBiomarkerReferences(self, catalog):
        results = catalog(object_provides=IProtocol.__identifier__)
        for i in results:
            obj = i.getObject()
            obj.biomarkers = []
    def ingest(self):
        request = plone.api.portal.get().REQUEST
        normalize = getUtility(IIDNormalizer).normalize
        context = aq_inner(self.context)
        biomarkerStatements = {}
        for url in context.rdfDataSources:
            biomarkerStatements.update(self.readRDF(url))
        # Start with a clean slate
        catalog, idUtil = plone.api.portal.get_tool('portal_catalog'), getUtility(IIntIds)
        results = catalog(
            path=dict(query='/'.join(context.getPhysicalPath()), depth=1),
            object_provides=IBiomarker.__identifier__
        )
        context.manage_delObjects([i.id for i in results])
        # Issue #20 — https://github.com/EDRN/P5/issues/20
        # Protocols have a ``biomarkers`` relation field, but the statement above just deleted all the
        # biomarkers. Since there's no ON DELETE CASCADE in Plone, we need to reset all protocols' fields
        # to empty so that when we repopulate them later we won't have bad values left over.
        self._removeProtocolToBiomarkerReferences(catalog)
        # Make all biomarker objects
        newBiomarkers, panels = {}, {}
        for uri, predicates in biomarkerStatements.iteritems():
            try:
                typeURI = predicates[rdflib.RDF.type][0]
                if typeURI != _biomarkerPredicateURI: continue
                isPanel = bool(int(predicates[_isPanelPredicateURI][0]))
                title = unicode(predicates[_bmTitlePredicateURI][0])
                hgnc = predicates[_hgncPredicateURI][0] if _hgncPredicateURI in predicates else None
                if hgnc is not None:
                    hgnc = hgnc.strip()
                objID = hgnc if hgnc else normalize(title)
                if isPanel:
                    fti, iface = 'eke.knowledge.biomarkerpanel', IBiomarkerPanel
                else:
                    fti, iface = 'eke.knowledge.elementalbiomarker', IElementalBiomarker
                obj = createContentInContainer(context, fti, id=objID, title=title, identifier=unicode(uri))
                newBiomarkers[uri] = obj
                if isPanel:
                    panels[uri] = obj
                    obj.members = []
                self.updateBiomarker(obj, fti, iface, predicates, context, biomarkerStatements, request)
            except KeyError:
                # Why does KeyError arise here?
                pass
        # Connect elementals to panels
        for uri, predicates in biomarkerStatements.iteritems():
            try:
                typeURI = predicates[rdflib.RDF.type][0]
                if typeURI != _biomarkerPredicateURI: continue
                panelURIs = predicates[_memberOfPanelPredicateURI]
                biomarker = newBiomarkers[uri]
                for panelURI in panelURIs:
                    panel = panels[panelURI]
                    panel.members.append(RelationValue(idUtil.getId(biomarker)))
                    notify(ObjectModifiedEvent(panel))
            except KeyError:
                # No _memberOfPanelPredicateURI, so skip
                pass
        # Add organ-specific information
        organSpecificStatements = self.readRDF(context.bmoDataSource)
        self.addOrganSpecificInformation(newBiomarkers, organSpecificStatements)
        if context.bmSumDataSource:
            context.dataSummary = self.getSummaryData(context.bmSumDataSource)
        # Set organ phases on each biomarker
        transaction.commit()
        results = catalog(object_provides=IBiomarkerBodySystem.__identifier__)
        for i in results:
            obj = i.getObject()
            updatePhases(obj, None)
        # Done
        publish(context)
        return IngestConsequences(newBiomarkers.values(), [], [])


class BiomarkerSummary(BrowserView):
    def __call__(self):
        context = aq_inner(self.context)
        self.request.response.setHeader('Content-type', 'application/json; charset=utf-8')
        self.request.response.setHeader('Content-Transfer-Encoding', '8bit')
        return context.dataSummary


@implementer(IVocabularyFactory)
class BodySystemsInBiomarkersVocabulary(object):
    u'''Vocabulary for body systems in biomarkers'''
    def __call__(self, context):
        catalog = plone.api.portal.get_tool('portal_catalog')
        results = catalog.uniqueValuesFor('indicatedBodySystems')
        vocabs = []
        for i in results:
            if i:
                vocabs.append((i, i))
        vocabs.sort()
        return SimpleVocabulary.fromItems(vocabs)
