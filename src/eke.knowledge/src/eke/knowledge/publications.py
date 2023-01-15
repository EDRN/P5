# encoding: utf-8

from .constants import MAX_URI_LENGTH, MAX_SLUG_LENGTH
from .knowledge import KnowledgeObject, KnowledgeFolder
from .utils import edrn_schema_uri as esu
from .utils import Ingestor as BaseIngestor
from Bio import Entrez
from contextlib import closing
from django.db import models
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.text import slugify
from django_plotly_dash import DjangoDash
from edrnsite.controls.models import Informatics
from html import escape as html_escape
from modelcluster.fields import ParentalKey
from plotly.express import bar
from rdflib import URIRef
from urllib.error import HTTPError
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable
from wagtail.models import Site
from wagtail.search import index
import dash_core_components as dcc
import dash_html_components as html
import pandas, re, logging


_logger = logging.getLogger(__name__)


class Publication(KnowledgeObject):
    template = 'eke.knowledge/publication.html'
    parent_page_types = ['ekeknowledge.PublicationIndex']
    page_description = 'Article, column, book, etc., of published scientific research'
    issue = models.CharField(max_length=50, blank=True, null=False, help_text='In what issue publication appeared')
    volume = models.CharField(max_length=50, blank=True, null=False, help_text='In what volume publication appeared')
    journal = models.CharField(max_length=250, blank=True, null=False, help_text='Name of the periodical')
    pubMedID = models.CharField(max_length=20, blank=True, null=False, help_text='Entrez Medline ID code number')
    year = models.IntegerField(blank=True, null=True, help_text='Year of publication')
    pubURL = models.URLField(blank=True, null=False, help_text='URL to read the publication')
    siteID = models.CharField(
        max_length=MAX_URI_LENGTH, blank=True, null=False,
        help_text='RDF subject URI of site that wrote the publication'
    )
    abstract = RichTextField(
        'abstract',
        blank=True, null=False,
        help_text='A summary of the contents of this publication'
    )

    def data_table(self) -> dict:
        '''Return the JSON-compatible dictionary describing this publication.'''
        return {'journal': self.journal, 'year': self.year, **super().data_table()}

    def get_context(self, request: HttpRequest, *args, **kwargs) -> dict:
        context = super().get_context(request, args, kwargs)
        appearances = []
        if self.journal: appearances.append(self.journal)
        if self.year: appearances.append(str(self.year))
        if self.volume: appearances.append(self.volume)
        appearances = ', '.join(appearances)
        if self.issue: appearances += ' ({})'.format(html_escape(self.issue))
        context['appearance'] = appearances
        return context
    content_panels = KnowledgeObject.content_panels + [
        FieldPanel('issue'),
        FieldPanel('volume'),
        FieldPanel('journal'),
        FieldPanel('pubMedID'),
        FieldPanel('year'),
        FieldPanel('pubURL'),
        FieldPanel('siteID'),
        FieldPanel('abstract'),
        InlinePanel('authors', label='Authors')
    ]
    search_fields = KnowledgeObject.search_fields + [
        # index.SearchField('abstract', partial_match=False),  # See if we can get biomarkers higher
        index.RelatedFields('authors', [index.SearchField('value')]),
        index.SearchField('journal'),
        index.FilterField('journal'),
        index.FilterField('year')
    ]
    class Meta:
        indexes = [models.Index(fields=['pubMedID']), models.Index(fields=['year'])]
    # Publications are special in that they don't use the RDFMeta and standard ingest "plumbing"
    # class RDFMeta:
    #     fields = {
    #         esu('year'): RDFAttribute('year', scalar=True),
    #         str(rdflib.DCTERMS.creator): RDFAttribute('authors', scalar=False, rel=False),
    #         **KnowledgeObject.RDFMeta.fields
    #     }


class Author(Orderable):
    '''An author of a publication.'''
    value = models.CharField(max_length=255, blank=False, null=False, default='Name', help_text='Author name')
    page = ParentalKey(Publication, on_delete=models.CASCADE, related_name='authors')
    panels = [FieldPanel('value')]


class Ingestor(BaseIngestor):
    '''Publications use a special ingest based on PubMedIDs and grant numbers, not the statements made in
    the RDF.
    '''
    _pubMedIDExpr         = re.compile(r'[0-9]+')                 # What PubMed IDs should look like
    _pubFetchSize         = 100                                   # How many pubs to get at once
    _grantSearchSize      = 10                                    # How many grants to get at once
    _pubMedPredicate      = URIRef(esu('pmid'))                   # RDF predicate for PubMed ID
    _siteIDPredicate      = URIRef(esu('site'))                   # RDF predicate for site ID
    _grantNumberURIPrefix = 'urn:edrn:knowledge:pub:via-grants:'  # How we'll identify pubs from grant numbers

    def slugify(self, pubMedID: str, title: str) -> str:
        '''Make an appropriate URI slug component for a publication.'''
        return slugify(f'{pubMedID} {title}')[:MAX_SLUG_LENGTH]

    def configureEntrez(self):
        '''Set up the Entrez API.

        Before we attempt to access Entrez for PubMed info, we need to configure it with our tool ID
        and an email address.
        '''
        informatics = Informatics.for_site(Site.objects.filter(is_default_site=True).first())
        Entrez.tool = informatics.entrez_id
        Entrez.email = informatics.entrez_email

    def addPublicationsBasedOnGrantNumbers(self, subjectURItoPMIDs: dict):
        '''Insert grant-based publications.

        This asks PubMed for publications based on the grant numbers in our PublicationIndex and adds
        them to ``subjectURItoPMIDs``.
        '''

        # This list→set→list makes grant numbers unique and in sliceable form:
        grantNumbers = list(set([i.value for i in self.folder.grant_numbers.all()]))

        if not grantNumbers:
            _logger.info('No grant numbers in %r, so skipping lookup of additional pubs', self.folder)
            return

        currentPMIDs = set([i[0] for i in subjectURItoPMIDs.values()])  # What pub med IDs do we have so far?
        missing      = set()                                            # And here's where we gather new ones

        def divide(grantNumbers):
            while len(grantNumbers) > 0:
                group, grantNumbers = grantNumbers[:self._grantSearchSize], grantNumbers[self._grantSearchSize:]
                yield group

        for group in divide(grantNumbers):
            searchTerm = u' OR '.join([u'({}[Grant Number])'.format(i) for i in group])
            # #80: PubMed API is really unreliable; try to press on even if it fails
            try:
                # FIXME: This'll break if it returns more than 9999 publications 😅
                with closing(Entrez.esearch(db='pubmed', rettype='medline', retmax=9999, term=searchTerm)) as es:
                    record = Entrez.read(es)
                    if not record: continue
                    pubMedIDs = set(record.get('IdList', []))
                    if not pubMedIDs: continue
                    missing |= pubMedIDs - currentPMIDs
            except HTTPError as ex:
                _logger.warning('Entrez search failed with %d for «%s» but pressing on', ex.getcode(), searchTerm)   
        for newPubMed in missing:
            subjectURItoPMIDs[self._grantNumberURIPrefix + newPubMed] = (newPubMed, '')

    def filterExistingPublications(self, subjectURItoPMIDs: dict):
        '''Remove existing publications from the to-do list.

        This finds all publications in our container by RDF subject URI and removes them from the
        ``subjectURItoPMIDs`` dictionary.
        '''
        results = Publication.objects.child_of(self.folder).filter(identifier__in=subjectURItoPMIDs.keys())
        for identifier in [i.identifier for i in results]:
            try:
                del subjectURItoPMIDs[identifier]
            except KeyError:
                # See https://github.com/EDRN/P5/issues/65
                pass

    def setAuthors(self, pub: Publication, medline):
        '''Annotate the ``pub`` with author information in the ``medline``.'''
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
        names.sort()
        pub.authors.add(*[Author(value=i) for i in names])

    def createMissingPublications(self, subjectURItoPMIDs: dict) -> set:
        '''Create publications described in ``subjectURItoPMIDs that are missing from our folder.

        Return a set of newly created Publications.
        '''
        def divvy(mapping):
            '''Divide the ``mapping`` into manageable groups.

            This helps us avoid overwhelming the Entrez API.
            '''
            items = list(mapping.items())
            while len(items) > 0:
                group, items = items[:self._pubFetchSize], items[self._pubFetchSize:]
                yield group

        for group in divvy(subjectURItoPMIDs):
            identifiers, pubInfo = [i[0] for i in group], [i[1] for i in group]
            identifiers.sort()
            # At this point identifiers is a sequence of unicode subjectUrIs and
            # pubInfo is a sequence of two-pair tuples of (unicode PubMedID, unicode site ID URI or None if unk)
            pubInfoDict = dict(pubInfo)
            # pubInfoDict is now a mapping of unicode PubMedID to unicode site ID URI (or None if unknwon)
            pubMedIDs = list(pubInfoDict.keys())
            pubMedIDs.sort()
            # pubMedIDs is a sequence of unicode PubMedIDs
            try:
                with closing(Entrez.efetch(db='pubmed', retmode='xml', rettype='medline', id=pubMedIDs)) as ef:
                    records = Entrez.read(ef)
                    for i in zip(identifiers, records['PubmedArticle']):
                        identifier, medline = str(i[0]), i[1]
                        pubMedID = str(medline['MedlineCitation']['PMID'])
                        # 🔮 TODO: find a better way to break these titles
                        # And maybe keep a separate full_title attribute
                        title = str(medline['MedlineCitation']['Article']['ArticleTitle'])[:250]
                        slug = self.slugify(pubMedID, title)
                        if Publication.objects.child_of(self.folder).filter(slug=slug).count() > 0:
                            _logger.debug('Publication %s “%s” already exists, skipping', pubMedID, slug)
                            continue
                        abstract = medline['MedlineCitation']['Article'].get('Abstract')
                        pub = Publication(
                            title=title, seo_title=title, draft_title=title, live=True,
                            slug=slug, identifier=identifier, pubMedID=pubMedID,
                            search_description='This is a publication by a member of the Early Detection Research Network.'
                        )
                        if abstract:
                            paragraphs = abstract.get('AbstractText', [])
                            if len(paragraphs) > 0:
                                pub.abstract = '\n'.join([u'<p>{}</p>'.format(html_escape(j)) for j in paragraphs])
                        issue = medline['MedlineCitation']['Article']['Journal']['JournalIssue'].get('Issue')
                        if issue: pub.issue = str(issue)
                        volume = medline['MedlineCitation']['Article']['Journal']['JournalIssue'].get('Volume')
                        if volume: pub.volume = str(volume)
                        year = medline['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate'].get('Year')
                        if year: pub.year = int(year)
                        try:
                            pub.journal = str(medline[u'MedlineCitation'][u'Article'][u'Journal'][u'ISOAbbreviation'])
                        except KeyError:
                            _logger.info(u'🤔 No journal with ISOAbbreviation available for pub %s', pubMedID)
                            pub.journal = u'«unknown»'
                        if pubInfoDict[pubMedID]: pub.siteID = pubInfoDict[pubMedID]
                        self.setAuthors(pub, medline)
                        self.folder.add_child(instance=pub)
                        pub.save()
            except HTTPError as ex:
                _logger.warning('Entrez retrieval failed with %d for «%r» but pressing on', ex.getcode(), pubMedIDs)
                _logger.debug('Entrez failed URL was «%s»', ex.geturl())
        return set()

    def ingest(self):
        self.configureEntrez()
        statements = self.readRDF()
        subjectURItoPMIDs, pmIDtoSubjectURIs = {}, {}
        for subjectURI, predicates in statements.items():
            pmID = str(predicates.get(self._pubMedPredicate, [''])[0]).strip()
            if not pmID or not self._pubMedIDExpr.match(pmID):
                _logger.warning('Got a weird "pubmed" ID «%s» from %s that looks wrong', pmID, subjectURI)
                continue
            if pmID in pmIDtoSubjectURIs:
                _logger.warning('PubMed %s already has pub %s but duplicating anyway', pmID, pmIDtoSubjectURIs[pmID])
                # At this point I would do
                #     continue
                # and skip making extra Publication objects except that some subject URIs from various
                # parts of the knowledge environment end up using the same pubmed ID and we have to
                # accommodate all of them
            siteID = str(predicates.get(self._siteIDPredicate, [''])[0])
            subjectURItoPMIDs[str(subjectURI)] = (pmID, siteID)
            pmIDtoSubjectURIs[pmID] = str(subjectURI)
        self.addPublicationsBasedOnGrantNumbers(subjectURItoPMIDs)
        self.filterExistingPublications(subjectURItoPMIDs)
        new = self.createMissingPublications(subjectURItoPMIDs)
        return new, set(), set()  # We only ever create new pubs; no updating or deleting


class PublicationIndex(KnowledgeFolder):
    '''A publication index is a container for Publications.'''

    template = 'eke.knowledge/publication-index.html'
    subpage_types = [Publication]
    page_description = 'Container for publications'

    def get_contents(self, request: HttpRequest):
        matches = Publication.objects.child_of(self).live().public().filter(year__isnull=False).order_by('-year')

        journals = request.GET.getlist('journal')
        if journals: matches = matches.filter(journal__in=journals)

        query = request.GET.get('query')
        if query: matches = matches.search(query)

        return matches

    def faceted_markup(self, request):
        pages, rows = self.get_contents(request), []
        for page in pages:
            rows.append(render_to_string('eke.knowledge/publication-row.html', {'publication': page.specific}))
        return ''.join(rows)

    def get_context(self, request: HttpRequest, *args, **kwargs) -> dict:
        context = super().get_context(request, *args, **kwargs)

        byYear = {}
        for publication in context['knowledge_objects']:
            if publication.year:
                count = byYear.get(publication.year, 0)
                count += 1
                byYear[publication.year] = count

        years, counts = [], []
        for year in sorted(byYear.keys()):
            years.append(year)
            counts.append(byYear[year])

        df = pandas.DataFrame({
            "Year": years,
            "# Publications": counts
        })
        figure = bar(df, x='Year', y='# Publications', barmode="group")

        APP_NAME = 'PubsByYear'
        app = DjangoDash(APP_NAME)
        app.layout = html.Div(children=[
            html.H4(children='Publication Frequency by Year'),
            dcc.Graph(id='publications-by-year', figure=figure)
        ])

        return context

    content_panels = KnowledgeFolder.content_panels + [InlinePanel('grant_numbers', label='Grant Numbers')]

    class Meta:
        pass
    class RDFMeta:
        ingestor = Ingestor
        types = {
            'http://edrn.nci.nih.gov/rdf/types.rdf#Publication': Publication,
        }


class GrantNumber(Orderable):
    '''An NIH-assigned funding identifier that identifies additional publications.'''
    value = models.CharField(max_length=20, blank=False, null=False, help_text='Grant Number')
    page = ParentalKey(PublicationIndex, on_delete=models.CASCADE, related_name='grant_numbers')
    panels = [FieldPanel('value')]
