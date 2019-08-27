# encoding: utf-8


u'''EKE Knowledge: Protocol Folder'''

from .base import Ingestor
from .knowledgefolder import IKnowledgeFolder, KnowledgeFolderView
from .protocol import IProtocol
from .site import ISite
from Acquisition import aq_inner
from five import grok
from plone.i18n.normalizer.interfaces import IIDNormalizer
from z3c.relationfield import RelationValue
from zope.component import getUtility
from zope.intid.interfaces import IIntIds
import urlparse, logging, plone.api, rdflib, dublincore, os.path


_logger = logging.getLogger(__name__)
_siteSpecificTypeURI = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/types.rdf#ProtocolSiteSpecific')
_projectFlagURI = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#projectFlag')
_leadInvestigatorSiteURI = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#leadInvestigatorSite')
_descriptionPredicates = (
    dublincore.DESCRIPTION_URI,
    rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#objective'),
    rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#aims'),
    rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#outcome')
)
_siteURIPrefix = u'http://edrn.nci.nih.gov/data/sites/'
_canonicalGroupNames = {
    u'Breast and Gynecologic Cancers Research': u'Breast and Gynecologic Cancers Research Group',
    u'G.I. and Other Associated Cancers Research Group': u'G.I. and Other Associated Cancers Research Group',
    u'Lung and Upper Aerodigestive Cancers Research Group': u'Lung and Upper Aerodigestive Cancers Research Group',
    u'Prostate and Urologic Cancers Research Group': u'Prostate and Urologic Cancers Research Group',
}


class IProtocolFolder(IKnowledgeFolder):
    u'''Protocol folder.'''


class ProtocolIngestor(Ingestor):
    grok.context(IProtocolFolder)
    def getInterfaceForContainedObjects(self, predicates):
        return IProtocol
    def getObjID(self, subjectURI, titles, predicates):
        if not titles: return None
        title = unicode(titles[0])
        if not title: return None
        normalize = getUtility(IIDNormalizer).normalize
        title = u'{}-{}'.format(urlparse.urlparse(subjectURI)[2].split('/')[-1], title)
        return normalize(title)
    def readRDF(self, url):
        u'''Read the RDF statements and return s/p/o dict'''
        unfiltered, filtered = super(ProtocolIngestor, self).readRDF(url), {}
        for subjectURI, predicates in unfiltered.iteritems():
            typeURI = predicates[rdflib.RDF.type][0]
            if typeURI != _siteSpecificTypeURI:
                filtered[subjectURI] = predicates
        return filtered
    def gatherProtocolToInvolvedInvestigatorSites(self):
        context = aq_inner(self.context)
        statements = {}
        for url in context.rdfDataSources:
            statements.update(super(ProtocolIngestor, self).readRDF(url))
        protocolToInvolvedSites = {}
        for uri, predicates in statements.iteritems():
            typeURI = predicates[rdflib.RDF.type][0]
            if typeURI == _siteSpecificTypeURI:
                protocolID, siteID = os.path.basename(urlparse.urlparse(unicode(uri)).path).split(u'-')
                siteIDs = protocolToInvolvedSites.get(protocolID, set())
                siteIDs.add(siteID)
                protocolToInvolvedSites[protocolID] = siteIDs
        return protocolToInvolvedSites
    def setInvolvedInvestigatorSites(self, protocol, protocolToInvolvedSites):
        catalog, idUtil = plone.api.portal.get_tool('portal_catalog'), getUtility(IIntIds)
        protocolID = os.path.basename(urlparse.urlparse(protocol.identifier).path).split(u'-')[0]
        siteNumbers = protocolToInvolvedSites.get(protocolID, [])
        siteIDs = [_siteURIPrefix + i for i in siteNumbers]
        brains = catalog(identifier=siteIDs, sort_on='sortable_title')
        for b in brains:
            site = b.getObject()
            siteIntID = idUtil.getId(b.getObject())
            if protocol.involvedInvestigatorSites is None: protocol.involvedInvestigatorSites = []
            protocol.involvedInvestigatorSites.append(RelationValue(siteIntID))
            piIdentifier = site.principalInvestigator.to_object.identifier if site.principalInvestigator else None
            if piIdentifier:
                currentIDs = set(protocol.investigatorIdentifiers if protocol.investigatorIdentifiers else [])
                if piIdentifier not in currentIDs:
                    currentIDs.add(piIdentifier)
                    protocol.investigatorIdentifiers = list(currentIDs)
    def ingest(self):
        context = aq_inner(self.context)
        catalog, portal = plone.api.portal.get_tool('portal_catalog'), plone.api.portal.get()
        consequences = super(ProtocolIngestor, self).ingest()

        catalog.reindexIndex('identifier', portal.REQUEST)
        protocolToInvolvedSites = self.gatherProtocolToInvolvedInvestigatorSites()
        for uri, predicates in consequences.statements.iteritems():
            if unicode(uri) == u'http://edrn.nci.nih.gov/data/protocols/0':
                # Bad data from DMCC
                continue
            results = catalog(identifier=unicode(uri), object_provides=IProtocol.__identifier__)
            objectID = self.getObjID(uri, None, predicates)
            isProject = unicode(predicates.get(_projectFlagURI, ['Protocol'])[0]) == u'Project'
            if len(results) == 1 or objectID in context.keys():
                # Existing protocol. Update it.
                if objectID in context.keys():
                    p = context[objectID]
                else:
                    p = results[0].getObject()
                # Fix the collaborative groups. The RDF from the DMCC contains comma-separated
                # collab group names which have all gone into item 0 of the group. We need
                # to split those into an actual list of ``n`` items and also fix the group names.
                cbs = p.collaborativeGroup
                if cbs is not None and len(cbs) == 1:
                    p.collaborativeGroup = [_canonicalGroupNames.get(i.strip(), u'Unknown') for i in cbs[0].split(u',')]
                elif cbs is None:
                    p.collaborativeGroup = []
                # Set project flag
                p.project = True if isProject else False
                # Set PI
                siteIdentifier = unicode(predicates.get(_leadInvestigatorSiteURI, [u''])[0])
                if siteIdentifier:
                    results = catalog(identifier=siteIdentifier, object_provides=ISite.__identifier__)
                    if len(results) == 1:
                        site = results[0].getObject()
                        p.piName = site.piName
                        p.principalInvestigator = site.principalInvestigator
                # Compute description
                for predicateName in _descriptionPredicates:
                    values = predicates.get(predicateName, [])
                    if values:
                        value = unicode(values[0])
                        if value:
                            p.description = value
                            break
                # And the involved sites
                self.setInvolvedInvestigatorSites(p, protocolToInvolvedSites)
        return consequences


class View(KnowledgeFolderView):
    grok.context(IProtocolFolder)
    # @memoize
    # def protocols(self):
    #     context = aq_inner(self.context)
    #     catalog = plone.api.portal.get_tool('portal_catalog')
    #     results = catalog(
    #         object_provides=IProtocol.__identifier__,
    #         path=dict(query='/'.join(context.getPhysicalPath()), depth=1),
    #         sort_on='sportable_title'
    #     )
    #     return [dict(booger=i.Title, description=i.Description, url=i.getURL(), piName=i.piName) for i in results]
