# encoding: utf-8

u'''Biomarker folder'''

from . import _
from .base import Ingestor
from .bodysystem import IBodySystem
from .biomarker import IBiomarker, IElementalBiomarker, IBiomarkerPanel, IBiomarkerBodySystem
from .knowledgefolder import IKnowledgeFolder, KnowledgeFolderView
from .utils import IngestConsequences, publish
from Acquisition import aq_inner
from five import grok
from plone.dexterity.utils import createContentInContainer
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.memoize.view import memoize
from z3c.relationfield import RelationValue
from zope import schema
from zope.component import getUtility, getMultiAdapter
from zope.intid.interfaces import IIntIds
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary
import urlparse, logging, plone.api, rdflib, dublincore

_logger = logging.getLogger(__name__)

# Specific URIs
_organPredicateURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Organ')
_bmOrganDataTypeURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#BiomarkerOrganData')
_accessPredicateURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#AccessGrantedTo')
_biomarkerTypeURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Biomarker')
_isPanelPredicateURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#IsPanel')
_bmTitlePredicateURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Title')
_hgncPredicateURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#HgncName')
_hasBiomarkerStudyDatasPredicateURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#hasBiomarkerStudyDatas')
_referencesStudyPredicateURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#referencesStudy')
_memberOfPanelPredicateURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#memberOfPanel')
_biomarkerPredicateURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Biomarker')
_certificationPredicateURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#certification')

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
    predicateURIBase + u'DecisionRule': ('decisionRule', False),
    predicateURIBase + u'Type': ('biomarkerType', False),
    predicateURIBase + u'Sensitivity': ('sensitivity', False),
    predicateURIBase + u'Specificity': ('specificity', False),
    predicateURIBase + u'NPV': ('npv', False),
    predicateURIBase + u'PPV': ('ppv', False),
    predicateURIBase + u'Prevalence': ('prevalence', False),
    predicateURIBase + u'SensSpecDetail': ('details', False),
    predicateURIBase + u'SpecificAssayType': ('specificAssayType', False),

    # For biomarker-body-systems
    predicateURIBase + u'PerformanceComment': ('performanceComment', False),
}


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
    # dataSummary = schema.TextLine(
    #     title=_(u'Biomarker Statistics'),
    #     description=_(u'Biomarker statistics.'),
    #     required=False
    # )
    disclaimer = schema.Text(
        title=_(u'Disclaimer'),
        description=_(u'Legal disclaimer to display on Biomarker Folder pages.'),
        required=False,
    )


class BiomarkerIngestor(Ingestor):
    grok.context(IBiomarkerFolder)
    def getInterfaceForContainedObjects(self):
        raise NotImplementedError(u'{} handles its ingest specially'.format(self.__class__.__name__))
    def _addBiomarkerToProtocol(self, biomarkerObj, protocolObj):
        pass
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
            # TODO: addBiomarkerToOrganGroup
            # TODO: _hasBiomarkerOrganStudyDatasPredicateURI
            certificationURIs = predicates.get(_certificationPredicateURI, [])
            for certificationURI in certificationURIs:
                if certificationURI == _cliaCertificationURI:
                    biomarkerBodySystem.cliaCertification = True
                elif certificationURI == _fdaCeritificationURI:
                    biomarkerBodySystem.fdaCertification = True
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
        # Make all biomarker objects
        newBiomarkers, panels = {}, {}
        for uri, predicates in biomarkerStatements.iteritems():
            try:
                typeURI = predicates[rdflib.RDF.type][0]
                if typeURI != _biomarkerTypeURI: continue
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
                if typeURI != _biomarkerTypeURI: continue
                panelURIs = predicates[_memberOfPanelPredicateURI]
                biomarker = newBiomarkers[uri]
                for panelURI in panelURIs:
                    panel = panels[panelURI]
                    panel.members.append(RelationValue(idUtil.getId(biomarker)))
            except KeyError:
                # No _memberOfPanelPredicateURI, so skip
                pass
        # Add organ-specific information
        organSpecificStatements = self.readRDF(context.bmoDataSource)
        self.addOrganSpecificInformation(newBiomarkers, organSpecificStatements)
        publish(context)
        return IngestConsequences(newBiomarkers.values(), [], [])


class BodySystemsVocabulary(object):
    u'''Vocabulary for body systems'''
    grok.implements(IVocabularyFactory)
    def __call__(self, context):
        catalog = plone.api.portal.get_tool('portal_catalog')
        results = catalog(object_provides=IBodySystem.__identifier__)
        vocabs = []
        for i in results:
            vocabs.append((i.Title, i.Title))
        return SimpleVocabulary.fromItems(vocabs)


grok.global_utility(BodySystemsVocabulary, name=u'eke.knowledge.vocabularies.BodySystemsVocabulary')
