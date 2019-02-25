# encoding: utf-8


u'''EKE Knowledge: Site Folder'''

from .base import Ingestor
from .knowledgefolder import IKnowledgeFolder, KnowledgeFolderView
from .site import ISite
from Acquisition import aq_inner
from five import grok
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.memoize.view import memoize
from zope.component import getUtility
import urlparse, logging, plone.api


_logger = logging.getLogger(__name__)
_memberTypeURI = u'http://edrn.nci.nih.gov/rdf/schema.rdf#memberType'
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


class ISiteFolder(IKnowledgeFolder):
    u'''Site folder.'''


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
        _logger.info("Site-overridden value setting pred %s to values %r for %s", predicate, values, fti)
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
                piURL = piName = None
                sites.append(dict(
                    title=brain.Title,
                    description=brain.Description,
                    investigator=piName,
                    piURL=piURL,
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
            # P5 doesn't have a uid_catalog
            # if i.piUID:
            #     uidBrain = uidCatalog(UID=i.piUID)[0]
            #     piURL = uidBrain.getURL(relative=False)
            #     piName = uidBrain.Title
            # else:
            #     piURL = piName = None
            piURL = piName = None
            sites[memberType].append(dict(
                title=i.Title,
                description=i.Description,
                investigator=piName,
                piURL=piURL,
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
