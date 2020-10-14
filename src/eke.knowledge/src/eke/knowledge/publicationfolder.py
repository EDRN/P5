# encoding: utf-8


u'''EKE Knowledge: Publication Folder'''

from . import _, ENTREZ_TOOL, ENTREZ_EMAIL
from .base import Ingestor
from .knowledgefolder import IKnowledgeFolder
from .publication import IPublication
from .utils import IngestConsequences, publish
from Acquisition import aq_inner
from Bio import Entrez
from plone.dexterity.utils import createContentInContainer
from plone.i18n.normalizer.interfaces import IIDNormalizer
from Products.Five import BrowserView
from zope import schema
from zope.component import getUtility
import contextlib, urllib2, rdflib, re, plone.api, cgi, logging

_logger = logging.getLogger(__name__)

# PubMed API
FETCH_GROUP_SIZE = 100  # Fetch this many publications in Entrez.fetch, pausing to construct objects between each
GRANT_SEARCH_SIZE = 10  # Search for this many grants at a timei n Entrez.search
Entrez.tool = ENTREZ_TOOL
Entrez.email = ENTREZ_EMAIL


# Constants
_pubMedExpr = re.compile(ur'[0-9]+')
_pmIDURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#pmid')
_siteIDURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#site')
_edrnGrantNumberURIPrefix = u'urn:edrn:knowledge:publication:via-grants:'


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
    grantNumbers = schema.List(
        title=_(u'Grant Numbers'),
        description=_(u'Funding identifiers or "grant numbers" of additional publications to create during routine ingest of the form «CA123456».'),
        required=False,
        default=[],
        value_type=schema.TextLine(
            title=_(u'Grant Number'),
            description=_(u'A grant number of the form «CA123456».')
        )
    )


class PublicationIngestor(Ingestor):
    def getInterfaceForContainedObjects(self, predicates):
        return IPublication
    def getSummaryData(self, source):
        with contextlib.closing(urllib2.urlopen(source)) as bytestring:
            return bytestring.read()
    def addPublicationsBasedOnGrantNumbers(self, subjectURItoPMIDs):
        u'''Add additional pubmeds based on grant numbers except if they're already represented in
        ``subjectURItoPMIDs``, creating new mappings as needed. Return a new mapping of subject
        URIs → pubmed IDs.
        '''
        context = aq_inner(self.context)
        grantNumbers = set(context.grantNumbers if context.grantNumbers else [])
        if not grantNumbers:
            _logger.info(u'No grant numbers in %r, so skipping looking up of grant numbers', context)
            return subjectURItoPMIDs

        currentPMIDs = set([i[0] for i in subjectURItoPMIDs.values()])  # What pub med IDs do we have so far?
        grantNumbers = set(grantNumbers)                                # Make grant numbers unique
        grantNumbers = list(grantNumbers)                               # And put them into a sliceable order
        missing      = set()                                            # And here's where we gather new ones

        def divide(grantNumbers):
            while len(grantNumbers) > 0:
                group, grantNumbers = grantNumbers[:GRANT_SEARCH_SIZE], grantNumbers[GRANT_SEARCH_SIZE:]
                yield group

        for group in divide(grantNumbers):
            searchTerm = u' OR '.join([u'({}[Grant Number])'.format(i) for i in group])
            # #80: PubMed API is really unreliable; try to press on even if it fails
            try:
                # FIXME: This'll break if it returns more than 9999 publications 😅
                with contextlib.closing(Entrez.esearch(db='pubmed', rettype='medline', retmax=9999, term=searchTerm)) as es:
                    record = Entrez.read(es)
                    if not record: continue
                    pubMedIDs = set(record.get('IdList', []))
                    if not pubMedIDs: continue
                    missing |= pubMedIDs - currentPMIDs
            except urllib2.HTTPError as ex:
                _logger.warning(u'Entrez search failed with %d for «%s» but pressing on', ex.getcode(), searchTerm)
                _logger.debug(u'Enterz failed URL was «%s»', ex.geturl())
        for newPubMed in missing:
            subjectURItoPMIDs[_edrnGrantNumberURIPrefix + newPubMed] = (newPubMed, u'')
        return subjectURItoPMIDs
    def filterExistingPublications(self, subjectURItoPMIDs):
        context = aq_inner(self.context)
        catalog = plone.api.portal.get_tool('portal_catalog')
        found = catalog(
            identifier=subjectURItoPMIDs.keys(),
            object_provides=IPublication.__identifier__,
            path=dict(query='/'.join(context.getPhysicalPath()), depth=1),
        )
        for f in found:
            try:
                del subjectURItoPMIDs[f.identifier]
            except KeyError:
                # See https://github.com/EDRN/P5/issues/65
                pass
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
            identifiers.sort()
            # At this point identifiers is a sequence of unicode subjectUrIs and
            # pubInfo is a sequence of two-pair tuples of (unicode PubMedID, unicode site ID URI or None if unk)
            pubInfoDict = dict(pubInfo)
            # pubInfoDict is now a mapping of unicode PubMedID to unicode site ID URI (or None if unknwon)
            pubMedIDs = pubInfoDict.keys()
            pubMedIDs.sort()
            # pubMedIDs is a sequence of unicode PubMedIDs
            try:
                _logger.info(u'E-fetching from Entrez %d PubMedIDs', len(pubMedIDs))
                with contextlib.closing(Entrez.efetch(db='pubmed', retmode='xml', rettype='medline', id=pubMedIDs)) as ef:
                    records = Entrez.read(ef)
                    for i in zip(identifiers, records[u'PubmedArticle']):
                        identifier, medline = unicode(i[0]), i[1]
                        pubMedID = unicode(medline[u'MedlineCitation'][u'PMID'])
                        title = unicode(medline[u'MedlineCitation'][u'Article'][u'ArticleTitle'])
                        objID = normalize(u'{} {}'.format(pubMedID, title))
                        if objID in context.keys():
                            _logger.info(u'Publication %s already exists; skipping', objID)
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
                        try:
                            pub.journal = unicode(medline[u'MedlineCitation'][u'Article'][u'Journal'][u'ISOAbbreviation'])
                        except KeyError:
                            _logger.info(u'🤔 No journal with ISOAbbreviation available for pub %s', pubMedID)
                            pub.journal = u'«unknown»'
                        year = medline[u'MedlineCitation'][u'Article'][u'Journal'][u'JournalIssue'][u'PubDate'].get(
                            u'Year', None
                        )
                        if year: pub.year = unicode(year)
                        if pubInfoDict[pubMedID]: pub.siteID = pubInfoDict[pubMedID]
                        pub.reindexObject()
                        created.append(pub)
            except urllib2.HTTPError as ex:
                _logger.warning(u'Entrez retreival failed with %d for «%r» but pressing on', ex.getcode(), pubMedIDs)
                _logger.debug(u'Enterz failed URL was «%s»', ex.geturl())
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
                # • "PMC***" which is wtf?
                # We choose to filter these out.
                if not pmID or not _pubMedExpr.match(pmID):
                    _logger.warning(
                        u'Got a weird "pubmed" ID "%s" from "%s" that doesn\'t look like a pubmed ID',
                        pmID,
                        subjectURI
                    )
                    continue
                if pmID in pmIDtoSubjectURIs:
                    _logger.warning(
                        u'PubMedID %s already represented by publication %s; but making a duplicate anyway',
                        pmID,
                        pmIDtoSubjectURIs[pmID]
                    )
                    # Argh! Normally I would want to do this:
                    #     continue
                    # except that other parts of the knowledge environment use various
                    # RDF subject URIs (like BMDB, eCAS) to link to what should be the
                    # same publication—and have the same pubmedID—but don't know any
                    # better. So for now, allow multiple Publication objects to exist
                    # even with the same pubmed ID just so we can address them with
                    # different RDF URI identifiers. Fuuuuuuuu—
                siteID = unicode(predicates.get(_siteIDURI, [u''])[0])
                subjectURItoPMIDs[unicode(subjectURI)] = (pmID, siteID)
                pmIDtoSubjectURIs[pmID] = unicode(subjectURI)

        subjectURItoPMIDs = self.addPublicationsBasedOnGrantNumbers(subjectURItoPMIDs)
        subjectURItoPMIDs = self.filterExistingPublications(subjectURItoPMIDs)
        created = self.createMissingPublications(subjectURItoPMIDs)
        # Add summary data
        if context.pubSumDataSource:
            context.dataSummary = self.getSummaryData(context.pubSumDataSource)
        else:
            context.dataSummary = u'{}'
        publish(context)
        return IngestConsequences(created=created, updated=[], deleted=[])


class PublicationSummary(BrowserView):
    def __call__(self):
        context = aq_inner(self.context)
        self.request.response.setHeader('Content-type', 'application/json; charset=utf-8')
        self.request.response.setHeader('Content-Transfer-Encoding', '8bit')
        return context.dataSummary
