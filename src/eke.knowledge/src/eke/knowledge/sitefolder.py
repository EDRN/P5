# encoding: utf-8


u'''EKE Knowledge: Site Folder'''

from . import _
from .base import Ingestor
from .knowledgefolder import IKnowledgeFolder, KnowledgeFolderView
from .site import ISite
from .utils import publish, setValue
from .person import IPerson
from Acquisition import aq_inner
from five import grok
from plone.dexterity.utils import createContentInContainer
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.memoize.view import memoize
from zope import schema
from zope.component import getUtility
import urlparse, logging, plone.api, rdflib


_logger = logging.getLogger(__name__)
_piURI = u'http://edrn.nci.nih.gov/rdf/schema.rdf#pi'
_memberTypeURI = u'http://edrn.nci.nih.gov/rdf/schema.rdf#memberType'
_surnamePredicateURI = rdflib.URIRef('http://xmlns.com/foaf/0.1/surname')
_middleNamePredicateURI = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#middleName')
_givenNamePredicateURI = rdflib.URIRef('http://xmlns.com/foaf/0.1/givenname')
_edrnSiteTypes = frozenset((
    u'Biomarker Reference Laboratories',
    u'Biomarker Developmental Laboratories',
    u'Clinical Validation Centers',
    u'Data Management and Coordinating Center',
    u'Informatics Center',
    u'National Cancer Institute',
    u'Associate Member A - EDRN Funded',
    u'Associate Member B',
    u'Associate Member C',
    u'SPOREs',
))
_personPredicates = (
    (rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#edrnTitle'), 'edrnTitle'),
    (rdflib.URIRef(u'http://www.w3.org/2001/vcard-rdf/3.0#fax'), 'fax'),
    (rdflib.URIRef(u'http://xmlns.com/foaf/0.1/accountName'), 'accountName'),
    (rdflib.URIRef(u'http://xmlns.com/foaf/0.1/mbox'), 'mbox'),
    (rdflib.URIRef(u'http://xmlns.com/foaf/0.1/phone'), 'phone'),
    (rdflib.URIRef(u'http://xmlns.com/foaf/0.1/surname'), 'surname'),
    (rdflib.URIRef(u'http://xmlns.com/foaf/0.1/givenname'), 'givenName'),
)
_personAddressPredicateSuffixes = (
    u'Address',
    u'Address2',
    u'City',
    u'Country',
    u'PostalCode',
    u'State',
)


class ISiteFolder(IKnowledgeFolder):
    u'''Site folder.'''
    peopleDataSources = schema.List(
        title=_(u'People RDF Data Sources'),
        description=_(u'URLs to sources of Resource Description Format (RDF) data for people.'),
        required=False,
        value_type=schema.URI(
            title=_(u'people RDF Data Source'),
            description=_(u'URL to a source of RDF data for people.'),
            required=False,
        )
    )


class SiteIngestor(Ingestor):
    grok.context(ISiteFolder)
    def getInterfaceForContainedObjects(self):
        return ISite
    def getObjID(self, subjectURI, titles, predicates):
        if not titles: return None
        title = unicode(titles[0])
        if not title: return None
        normalize = getUtility(IIDNormalizer).normalize
        title = u'%s %s' % (urlparse.urlparse(subjectURI)[2].split('/')[-1], title)
        return normalize(title)
    def setValue(self, obj, fti, iface, predicate, predicateMap, values):
        if unicode(predicate) == _memberTypeURI:
            if values:
                memberType = values[0]
                memberType = memberType.strip()
                if memberType.startswith(u'Associate Member C') or memberType.startswith(u'Assocaite Member C'):
                    # Thanks DMCC
                    memberType = u'Associate Member C'
                elif memberType.startswith(u'Associate Member B'):
                    memberType = u'Associate Member B'
                elif memberType == u'Biomarker Developmental  Laboratories':
                    # Thanks DMCC
                    memberType = u'Biomarker Developmental Laboratories'
                elif memberType == u'SPORE':
                    # CA-697
                    memberType = u'SPOREs'
                values = [memberType]
        super(SiteIngestor, self).setValue(obj, fti, iface, predicate, predicateMap, values)
    def getPredicateValue(self, predicateURI, predicates):
        u'''Return a single unicode value from the ``predicates`` matching the given
        ``predicateURI or an empty unicode string if not found.'''
        if predicateURI in predicates:
            return unicode(predicates[predicateURI][0])
        else:
            return u''
    def getNameComponents(self, predicates):
        return (
            self.getPredicateValue(_surnamePredicateURI, predicates),
            self.getPredicateValue(_givenNamePredicateURI, predicates),
            self.getPredicateValue(_middleNamePredicateURI, predicates)
        )
    def createPersonTitle(self, predicates):
        last, first, middle = self.getNameComponents(predicates)
        given = first
        if not given:
            given = middle
        else:
            if middle:
                given += ' ' + middle
        if not given:
            return last
        else:
            return u'{}, {}'.format(last, given)
    def createPerson(self, context, identifier, predicates):
        person = createContentInContainer(
            context,
            'eke.knowledge.person',
            title=self.createPersonTitle(predicates),
            identifier=identifier,
        )
        for predicate, fieldName in _personPredicates:
            if predicate in predicates:
                values = predicates.get(predicate)
                if values:
                    value = unicode(values[0])
                    if value:
                        setattr(person, fieldName, value)
        return person
    def ingest(self):
        u'''Override Ingestor.ingest so we can handle people'''
        context = aq_inner(self.context)
        catalog, portal = plone.api.portal.get_tool('portal_catalog'), plone.api.portal.get()
        consequences = super(SiteIngestor, self).ingest()
        siteStatments = consequences.statements
        _logger.info('At this point, we got %r', consequences)
        catalog.reindexIndex('identifier', portal.REQUEST)
        peopleStatements = {}
        peopleDataSources = context.peopleDataSources if context.peopleDataSources is not None else []
        for personURL in peopleDataSources:
            peopleStatements.update(self.readRDF(personURL))
        for siteIdentifier, predicates in siteStatments.iteritems():
            piPredicateURI = rdflib.URIRef(_piURI)
            if piPredicateURI in predicates:
                pis = predicates[piPredicateURI]
                if len(pis) > 0 and pis[0]:
                    piIdentifier = pis[0]
                    if piIdentifier in peopleStatements:
                        results = catalog(identifier=unicode(siteIdentifier))
                        if len(results) > 1:
                            _logger.critical('Got multiple matches for %s', unicode(siteIdentifier))
                        elif len(results) == 0:
                            _logger.critical('Just created site %s not found in catalog', unicode(siteIdentifier))
                        else:
                            siteBrain = results[0]
                            results = catalog(identifier=unicode(piIdentifier))
                            if len(results) == 0:
                                site = siteBrain.getObject()
                                person = self.createPerson(site, piIdentifier, peopleStatements[piIdentifier])
                                if person is not None:
                                    site.principalInvestigator = person
                                    site.piObjectID = person.id
                                    site.piName = person.title
                                    consequences.created.append(person)
        _logger.warn('Got %d site statements, %d people statements', len(siteStatments), len(peopleStatements))
        publish(context)
        return consequences


class View(KnowledgeFolderView):
    grok.context(ISiteFolder)
    def _sortByInvestigator(self, sitesList):
        sitesList.sort(lambda a, b: cmp(a['investigator'], b['investigator']))
    def _sortBySiteName(self, sitesList):
        sitesList.sort(lambda a, b: cmp(a['title'], b['title']))
    def _transformTypeName(self, memberType):
        if memberType.startswith(u'Associate Member C') or memberType.startswith(u'Assocaite Member C'):  # Thanks, DMCC
            return u'Associate Member C'
        elif memberType.startswith(u'Associate Member B'):
            return u'Associate Member B'
        elif memberType == u'Clinical Validation Center':
            return u'Clinical Validation Centers'  # CA-680
        elif memberType == u'SPORE':
            return u'SPOREs'  # CA-697
        else:
            return unicode(memberType)
    @memoize
    def biomarkerDevelopmentalLaboratories(self):
        context = aq_inner(self.context)
        catalog = plone.api.portal.get_tool('portal_catalog')
        # uidCatalog = plone.api.portal.get_tool('uid_catalog')
        results = catalog(
            object_provides=ISite.__identifier__,
            path=dict(query='/'.join(context.getPhysicalPath()), depth=1),
            memberType=(u'Biomarker Developmental Laboratories', u'Biomarker Developmental  Laboratories')  # Thanks, DMCC
        )
        byOrgan = {}
        for brain in results:
            organNames = brain.organs if brain.organs is not None and len(brain.organs) > 0 else ('',)
            for organName in organNames:
                if organName not in byOrgan: byOrgan[organName] = {}
                proposals = byOrgan[organName]
                if brain.proposal not in proposals: proposals[brain.proposal] = []
                sites = proposals[brain.proposal]
                # P5 doesn't have a uid_catalog
                # if brain.piUID:
                #     uidBrain = uidCatalog(UID=brain.piUID)[0]
                #     piURL = uidBrain.getURL(relative=False)
                #     piName = uidBrain.Title
                # else:
                #     piURL = piName = None
                sites.append(dict(
                    title=brain.Title,
                    description=brain.Description,
                    investigator=brain.piName,
                    piObjectID=brain.piObjectID,
                    url=brain.getURL(),
                    specialty=brain.specialty
                ))
        organs = []
        for organName, proposals in byOrgan.items():
            propGroup = []
            for proposalName, sites in proposals.items():
                propGroup.append(dict(title=proposalName, sites=sites))
            propGroup.sort(lambda a, b: (not a['title'] and not b['title']) and 1 or cmp(a['title'], b['title']))
            organs.append(dict(title=organName, proposalGroups=propGroup))
        organs.sort(lambda a, b: (not a['title'] and not b['title']) and 1 or cmp(a['title'], b['title']))
        return organs
    @memoize
    def biomarkerReferenceLaboratories(self):
        allSites = self._sites()
        try:
            brls = allSites[u'Biomarker Reference Laboratories']
            self._sortByInvestigator(brls)
            return brls
        except KeyError:
            return []
    @memoize
    def clinicalValidationCenters(self):
        allSites = self._sites()
        try:
            cvcs = allSites[u'Clinical Validation Centers']
            self._sortByInvestigator(cvcs)
            return cvcs
        except KeyError:
            return []
    @memoize
    def dmccSites(self):
        allSites = self._sites()
        try:
            dmccs = allSites[u'Data Management and Coordinating Center']
            self._sortBySiteName(dmccs)
            return dmccs
        except KeyError:
            return []
    @memoize
    def icSites(self):
        allSites = self._sites()
        try:
            ics = allSites[u'Informatics Center']
            self._sortBySiteName(ics)
            return ics
        except KeyError:
            return []
    def nciSites(self):
        allSites = self._sites()
        try:
            ncis = allSites[u'National Cancer Institute']
            self._sortByInvestigator(ncis)
            return ncis
        except KeyError:
            return []
    def typeASites(self):
        allSites = self._sites()
        try:
            sites = allSites[u'Associate Member A - EDRN Funded']
            self._sortBySiteName(sites)
            return sites
        except KeyError:
            return []
    def typeBSites(self):
        allSites = self._sites()
        try:
            sites = allSites[u'Associate Member B']
            self._sortBySiteName(sites)
            return sites
        except KeyError:
            return []
    def typeCSites(self):
        allSites = self._sites()
        try:
            sites = allSites[u'Associate Member C']
            self._sortBySiteName(sites)
            return sites
        except KeyError:
            return []
    def sporeSites(self):
        allSites = self._sites()
        try:
            sites = allSites[u'SPOREs']
            self._sortBySiteName(sites)
            return sites
        except KeyError:
            return []
    def otherSites(self):
        allSites, otherSites = self._sites(), {}
        for memberType, sites in allSites.items():
            if memberType not in _edrnSiteTypes:
                otherSites[memberType] = sites
                self._sortBySiteName(sites)
        otherSites = [dict(memberType=memberType, sites=sites) for memberType, sites in otherSites.items()]
        otherSites.sort(lambda a, b: cmp(a['memberType'], b['memberType']))
        return otherSites
    @memoize
    def _sites(self):
        context = aq_inner(self.context)
        catalog = plone.api.portal.get_tool('portal_catalog')
        # uidCatalog = plone.api.portal.get_tool('uid_catalog')
        results = catalog(
            object_provides=ISite.__identifier__,
            path=dict(query='/'.join(context.getPhysicalPath()), depth=1),
            sort_on='memberType'
        )
        sites = {}
        for i in results:
            memberType = self._transformTypeName(i.memberType.strip())
            if not memberType:
                # CA-609: skip 'em
                continue
            if memberType not in sites:
                sites[memberType] = []
            sites[memberType].append(dict(
                title=i.Title,
                description=i.Description,
                investigator=i.piName,
                organs=i.organs,
                proposal=i.proposal,
                url=i.getURL(),
                specialty=i.specialty
            ))
        return sites
    @memoize
    def subfolders(self):
        context = aq_inner(self.context)
        catalog = plone.api.portal.get_tool('portal_catalog')
        results = catalog(
            object_provides=ISiteFolder.__identifier__,
            path=dict(query='/'.join(context.getPhysicalPath()), depth=1),
            sort_on='sortable_title'
        )
        return [dict(title=i.Title, description=i.Description, url=i.getURL()) for i in results]
