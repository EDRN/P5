# encoding: utf-8


u'''EKE Knowledge: Publication Folder'''

from . import _, ENTREZ_TOOL, ENTREZ_EMAIL
from .base import Ingestor
from .knowledgefolder import IKnowledgeFolder
from .publication import IPublication
from Acquisition import aq_inner
from .utils import IngestConsequences, publish
from Bio import Entrez
from plone.i18n.normalizer.interfaces import IIDNormalizer
from zope.component import getUtility
from five import grok
from plone.dexterity.utils import createContentInContainer
from zope import schema
import contextlib, urllib2, rdflib, re, plone.api, cgi, logging

_logger = logging.getLogger(__name__)

# PubMed API
FETCH_GROUP_SIZE = 100  # Fetch this many publications in Entrez.fetch, pausing to construct objects between each
Entrez.tool = ENTREZ_TOOL
Entrez.email = ENTREZ_EMAIL


# Constants
_pubMedExpr = re.compile(ur'[0-9]+')
_pmIDURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#pmid')
_siteIDURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#site')


class IPublicationFolder(IKnowledgeFolder):
    u'''Publication folder.'''
    pubSumDataSource = schema.TextLine(
        title=_(u'Summary Data Source'),
        description=_(u'URL to a source of summary statistics that describes publications in this folder.'),
        required=False,
    )
    dataSummary = schema.Text(
        title=_(u'Data Summary'),
        description=_(u'JSON data that describe summary information for the data in this folder.'),
        required=False,
    )


class PublicationIngestor(Ingestor):
    grok.context(IPublicationFolder)
    def getInterfaceForContainedObjects(self, predicates):
        return IPublication
    def getSummaryData(self, source):
        with contextlib.closing(urllib2.urlopen(source)) as bytestring:
            return bytestring.read()
    def filterExistingPublications(self, subjectURItoPMIDs):
        context = aq_inner(self.context)
        catalog = plone.api.portal.get_tool('portal_catalog')
        found = catalog(
            identifier=subjectURItoPMIDs.keys(),
            object_provides=IPublication.__identifier__,
            path=dict(query='/'.join(context.getPhysicalPath()), depth=1),
        )
        for f in found:
            del subjectURItoPMIDs[f.identifier]
        return subjectURItoPMIDs
    def divvy(self, subjectURItoPMIDs):
        subjectURItoPMIDs = subjectURItoPMIDs.items()
        while len(subjectURItoPMIDs) > 0:
            group, subjectURItoPMIDs = subjectURItoPMIDs[:FETCH_GROUP_SIZE], subjectURItoPMIDs[FETCH_GROUP_SIZE:]
            yield group
    def setAuthors(self, pub, medline):
        authorList = medline[u'MedlineCitation'][u'Article'].get(u'AuthorList', [])
        names = []
        for author in authorList:
            lastName = author.get(u'LastName', None)
            if not lastName:
                initials = author.get(u'Initials', None)
                if not initials: continue
            initials = author.get(u'Initials', None)
            name = u'{} {}'.format(lastName, initials) if initials else lastName
            names.append(name)
        pub.authors = names
    def createMissingPublications(self, subjectURItoPMIDs):
        context = aq_inner(self.context)
        normalize = getUtility(IIDNormalizer).normalize
        created = []
        for group in self.divvy(subjectURItoPMIDs):
            identifiers, pubInfo = [i[0] for i in group], [i[1] for i in group]
            # At this point identifiers is a sequence of unicode subjectUrIs and
            # pubInfo is a sequence of two-pair tuples of (unicode PubMedID, unicode site ID URI or None if unk)
            pubInfoDict = dict(pubInfo)
            # pubInfoDict is now a mapping of unicode PubMedID to unicode site ID URI (or None if unknwon)
            pubMedIDs = pubInfoDict.keys()
            # pubMedIDs is a sequence of unicode PubMedIDs
            _logger.info(u'E-fetching from Entrez %d PubMedIDs', len(pubMedIDs))
            with contextlib.closing(Entrez.efetch(db='pubmed', retmode='xml', rettype='medline', id=pubMedIDs)) as ef:
                records = Entrez.read(ef)
                for i in zip(identifiers, records[u'PubmedArticle']):
                    identifier, medline = unicode(i[0]), i[1]
                    pubMedID = unicode(medline[u'MedlineCitation'][u'PMID'])
                    title = unicode(medline[u'MedlineCitation'][u'Article'][u'ArticleTitle'])
                    objID = normalize(u'{} {}'.format(pubMedID, title))
                    if objID in context.keys():
                        _logger.info(u'Publiation %s already exists; skipping', objID)
                    pub = createContentInContainer(
                        context,
                        'eke.knowledge.publication',
                        id=objID,
                        identifier=identifier,
                        title=title,
                        pubMedID=pubMedID
                    )
                    abstract = medline[u'MedlineCitation'][u'Article'].get(u'Abstract', None)
                    if abstract:
                        paragraphs = abstract.get(u'AbstractText', [])
                        if len(paragraphs) > 0:
                            pub.abstract = u'\n'.join([u'<p>{}</p>'.format(cgi.escape(j)) for j in paragraphs])
                    self.setAuthors(pub, medline)
                    issue = medline[u'MedlineCitation'][u'Article'][u'Journal'][u'JournalIssue'].get(u'Issue', None)
                    if issue: pub.issue = unicode(issue)
                    volume = medline[u'MedlineCitation'][u'Article'][u'Journal'][u'JournalIssue'].get(u'Volume', None)
                    if volume: pub.volume = unicode(volume)
                    pub.journal = unicode(medline[u'MedlineCitation'][u'Article'][u'Journal'][u'ISOAbbreviation'])
                    year = medline[u'MedlineCitation'][u'Article'][u'Journal'][u'JournalIssue'][u'PubDate'].get(
                        u'Year', None
                    )
                    if year: pub.year = unicode(year)
                    if pubInfoDict[pubMedID]: pub.siteID = pubInfoDict[pubMedID]
                    pub.reindexObject()
                    created.append(pub)
        return created
    def ingest(self):
        context = aq_inner(self.context)

        # TODO: Idea: do a "best effort" ingest using the following line:
        # consequences = super(PublicationIngestor, self).ingest()
        # then use PubMed to refine the data???

        # Use what PubMed IDs we can get for now:
        subjectURItoPMIDs, pmIDtoSubjectURIs = {}, {}
        for rdfDataSource in context.rdfDataSources:
            statements = self.readRDF(rdfDataSource)
            for subjectURI, predicates in statements.iteritems():
                pmID = unicode(predicates.get(_pmIDURI, [u''])[0])
                pmID = pmID.strip()
                # DMCC uses some bizarre PubMedIDs, including:
                # • "Not Available Yet"
                # • "N/A"
                # • "N/A-not peer reviewed"
                # We choose to filter these out.
                if not pmID or not _pubMedExpr.match(pmID): continue
                if pmID in pmIDtoSubjectURIs:
                    _logger.warning(
                        u'PubMedID %s already represented by publication %s; ignoring',
                        pmID,
                        pmIDtoSubjectURIs[pmID]
                    )
                    continue
                siteID = unicode(predicates.get(_siteIDURI, [u''])[0])
                subjectURItoPMIDs[unicode(subjectURI)] = (pmID, siteID)
                pmIDtoSubjectURIs[pmID] = unicode(subjectURI)
        subjectURItoPMIDs = self.filterExistingPublications(subjectURItoPMIDs)
        created = self.createMissingPublications(subjectURItoPMIDs)
        # Add summary data
        if context.pubSumDataSource:
            context.dataSummary = self.getSummaryData(context.pubSumDataSource)
        else:
            context.dataSummary = u'{}'
        publish(context)
        return IngestConsequences(created=created, updated=[], deleted=[])


class PublicationSummary(grok.View):
    grok.context(IPublicationFolder)
    grok.require('zope2.View')
    grok.name('summary')
    def render(self):
        context = aq_inner(self.context)
        self.request.response.setHeader('Content-type', 'application/json; charset=utf-8')
        self.request.response.setHeader('Content-Transfer-Encoding', '8bit')
        return context.dataSummary
