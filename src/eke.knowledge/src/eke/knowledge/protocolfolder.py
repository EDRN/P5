# encoding: utf-8


u'''EKE Knowledge: Site Folder'''

from .base import Ingestor
from .knowledgefolder import IKnowledgeFolder, KnowledgeFolderView
from .protocol import IProtocol
from .site import ISite
from Acquisition import aq_inner
from five import grok
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.memoize.view import memoize
from zope.component import getUtility
import urlparse, logging, plone.api, rdflib


_logger = logging.getLogger(__name__)
_siteSpecificTypeURI = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/types.rdf#ProtocolSiteSpecific')
_projectFlagURI = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#projectFlag')
_leadInvestigatorSiteURI = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#leadInvestigatorSite')


class IProtocolFolder(IKnowledgeFolder):
    u'''Protocol folder.'''


class ProtocolIngestor(Ingestor):
    grok.context(IProtocolFolder)
    def getInterfaceForContainedObjects(self):
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
    def ingest(self):
        context = aq_inner(self.context)
        catalog, portal = plone.api.portal.get_tool('portal_catalog'), plone.api.portal.get()
        consequences = super(ProtocolIngestor, self).ingest()
        catalog.reindexIndex('identifier', portal.REQUEST)
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
                p.project = True if isProject else False
                siteIdentifier = unicode(predicates.get(_leadInvestigatorSiteURI, [u''])[0])
                if siteIdentifier:
                    results = catalog(identifier=siteIdentifier, object_provides=ISite.__identifier__)
                    if len(results) == 1:
                        p.piName = results[0].getObject().piName
        return consequences


class View(KnowledgeFolderView):
    grok.context(IProtocolFolder)
    @memoize
    def protocols(self):
        context = aq_inner(self.context)
        catalog = plone.api.portal.get_tool('portal_catalog')
        results = catalog(
            object_provides=IProtocol.__identifier__,
            path=dict(query='/'.join(context.getPhysicalPath()), depth=1),
            sort_on='sportable_title'
        )
        return [dict(title=i.Title, description=i.Description, url=i.getURL(), piName=i.piName) for i in results]
