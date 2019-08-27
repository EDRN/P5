# encoding: utf-8


u'''EKE Knowledge: Site Folder'''

from . import _
from .base import Ingestor
from .knowledgefolder import IKnowledgeFolder, KnowledgeFolderView
from .site import ISite
from .utils import publish
from Acquisition import aq_inner
from five import grok
from plone.dexterity.utils import createContentInContainer
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.memoize.view import memoize
from z3c.relationfield import RelationValue
from zope import schema
from zope.component import getUtility
from zope.intid.interfaces import IIntIds
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent, ObjectAddedEvent
import urlparse, logging, plone.api, rdflib


_logger = logging.getLogger(__name__)
_piURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#pi')
_coPIURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#copi')
_coIURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#coi')
_iURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#investigator')
_memberTypeURI = u'http://edrn.nci.nih.gov/rdf/schema.rdf#memberType'
_surnamePredicateURI = rdflib.URIRef(u'http://xmlns.com/foaf/0.1/surname')
_middleNamePredicateURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#middleName')
_givenNamePredicateURI = rdflib.URIRef(u'http://xmlns.com/foaf/0.1/givenname')
_siteURI = rdflib.URIRef(u'http://edrn.nci.nih.gov/rdf/schema.rdf#site')
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
    def getInterfaceForContainedObjects(self, predicates):
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
        personTitle = self.createPersonTitle(predicates)
        personID = getUtility(IIDNormalizer).normalize(personTitle)
        if personID in context:
            context.manage_delObjects([personID])
        person = createContentInContainer(
            context,
            'eke.knowledge.person',
            id=personID,
            title=personTitle,
            identifier=unicode(identifier),
        )
        getUtility(IIntIds).register(person)  # WHY IS THIS NEEDED?
        for predicate, fieldName in _personPredicates:
            if predicate in predicates:
                values = predicates.get(predicate)
                if values:
                    value = unicode(values[0])
                    if value:
                        setattr(person, fieldName, value)
        # Enable display of pubs on a person later on:
        person.siteID = person.aq_parent.identifier
        notify(ObjectAddedEvent(person))
        return person
    def _ingestPeople(self, statements, sites):
        u'''The ``statements`` are the "spo" dict: ``{rdflib.term.URIRef subj: {rdflib.term.URIRef pred: [values]}}``
        where subj is a subject URI and pred is a predicate URI, while values may be either rdflib.term.Literal
        for literal objects or rdflib.term.URIRef for reference objects, while ``sites`` is a dict from unicode
        site URI to siteObj. Return a mapping of uri to people objects.'''
        createdPeople = {}
        for uri, predicates in statements.iteritems():
            if _siteURI not in predicates:
                _logger.info(u"Person %s doesn't have a site; skipping", unicode(uri))
                continue
            siteURI = [unicode(i) for i in predicates[_siteURI]][0]
            if siteURI not in sites:
                _logger.info(u"Person %s has a site %s that is unknown; skipping", unicode(uri), siteURI)
                continue
            site = sites[unicode(siteURI)]
            person = self.createPerson(site, uri, predicates)
            createdPeople[unicode(uri)] = person
        return createdPeople
    def addInvestigators(self, siteURI, sites, personPredicate, people, sitePredicates, fieldName, multiValued):
        siteURI = unicode(siteURI)
        if siteURI not in sites: return
        site = sites[siteURI]
        if personPredicate not in sitePredicates: return
        personURIs = [unicode(i) for i in sitePredicates[personPredicate]]
        # Normally I'd do this:
        #
        #     personIDs = [getUtility(IIntIds).getId(people[personURI]) for personURI in personURIs]
        #
        # But five.intid is sometimes giving this:
        #
        #       File "Documents/Clients/JPL/Cancer/Portal/Development/P5/src/eke.knowledge/src/eke/knowledge/sitefolder.py", line 181, in addInvestigators
        #         personIDs = [getUtility(IIntIds).getId(people[personURI]) for personURI in personURIs]
        #       File ".buildout/eggs/five.intid-1.1.2-py2.7.egg/five/intid/intid.py", line 41, in getId
        #         return z3IntIds.getId(self, ob)
        #       File ".buildout/eggs/zope.intid-3.7.2-py2.7.egg/zope/intid/__init__.py", line 89, in getId
        #         raise KeyError(ob)
        #     KeyError: <Item at /edrn/sites/202-fox-chase-cancer-center/engstrom-paul>
        #
        # So we'll do a "best effort":
        personIDs = []
        for personURI in personURIs:
            try:
                personIDs.append(getUtility(IIntIds).getId(people[personURI]))
            except KeyError:
                pass
        if multiValued:
            setattr(site, fieldName, [RelationValue(personID) for personID in personIDs])
        else:
            setattr(site, fieldName, RelationValue(personIDs[0]))
        notify(ObjectModifiedEvent(site))
    def ingest(self):
        u'''Override Ingestor.ingest so we can handle people'''
        consequences = super(SiteIngestor, self).ingest()
        context = aq_inner(self.context)
        catalog, portal = plone.api.portal.get_tool('portal_catalog'), plone.api.portal.get()
        sites = {}
        for siteObj in consequences.created + consequences.updated:
            sites[siteObj.identifier] = siteObj
        siteStatements = consequences.statements
        _logger.info('At this point, we got %r', consequences)
        catalog.reindexIndex('identifier', portal.REQUEST)
        peopleStatements = {}
        peopleDataSources = context.peopleDataSources if context.peopleDataSources is not None else []
        for personURL in peopleDataSources:
            peopleStatements.update(self.readRDF(personURL))
        people = self._ingestPeople(peopleStatements, sites)
        consequences.created.extend(people.values())
        for siteURI, predicates in siteStatements.iteritems():
            # Set up investigators
            self.addInvestigators(siteURI, sites, _piURI, people, predicates, 'principalInvestigator', False)
            self.addInvestigators(siteURI, sites, _coPIURI, people, predicates, 'coPrincipalInvestigators', True)
            self.addInvestigators(siteURI, sites, _coIURI, people, predicates, 'coInvestigators', True)
            self.addInvestigators(siteURI, sites, _iURI, people, predicates, 'investigators', True)
            # While we're here, set the piName, piObjectID
            try:
                site = sites[unicode(siteURI)]
            except KeyError:
                # Subsequent ingest and no updated needed
                continue
            try:
                site.piName = people[unicode(predicates[_piURI][0])].title
                site.piObjectID = people[unicode(predicates[_piURI][0])].id
            except (KeyError, IndexError):
                # We tried
                pass
            # While we're here, set the siteID
            site.dmccSiteID = urlparse.urlparse(siteURI)[2].split(u'/')[-1]
            # While we're here, set the de-normalized people fields
            for person in [site[p] for p in site.keys()]:
                person.siteName = site.title
                person.piName = site.piName
                person.memberType = site.memberType
            # TODO: DO THIS!
        # XXX WHY? catalog.reindexIndex('siteID', portal.REQUEST)
        _logger.warn('Got %d site statements, %d people statements', len(siteStatements), len(peopleStatements))
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
                piObjectID=i.piObjectID,
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
