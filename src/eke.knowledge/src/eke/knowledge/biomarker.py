# encoding: utf-8

u'''Biomarkers'''

from . import _
from .bodysystem import IBodySystem
from .dataset import IDataset
from .knowledgeobject import IKnowledgeObject
from .protocol import IProtocol
from .publication import IPublication
from .resource import IResource
from .utils import generateVocabularyFromIndex
from Acquisition import aq_inner
from collective import dexteritytextindexer
from plone.app.vocabularies.catalog import CatalogSource
from plone.memoize.view import memoize
from Products.Five import BrowserView
from z3c.relationfield.schema import RelationChoice, RelationList
from zope import schema
from zope.interface import implementer
from zope.interface import Interface
from zope.schema.interfaces import IVocabularyFactory
import plone.api

CURATED_SECTIONS = {
    'Organs': True,
    'Studies': False,
    'Publications': True,
    'Resources': True,
    'Biomuta': True,
    'Organs-Supplemental': False,
}


class IQualityAssuredObject(Interface):
    u'''An abstract object that undergoes a quality assurance process.'''
    qaState = schema.TextLine(
        title=_(u'QA State'),
        description=_(u'The current status with regard to quality assurance of this object.'),
        required=False,
    )


class IPhasedObject(Interface):
    u'''An abstract object that undergoes the standard phases of biomarker research.'''
    phase = schema.TextLine(
        title=_(u'Phase'),
        description=_(u"The current phase of the biomarker's development with regard to this organ."),
        required=False,
    )


class IResearchedObject(Interface):
    u'''An abstract object that is researched; that is, there are studies,
    publications, datasets, and other resources about it.'''
    protocols = RelationList(
        title=_(u'Protocols'),
        description=_(u'Protocols (and studies) that are studying this object.'),
        default=[],
        required=False,
        value_type=RelationChoice(
            title=_(u'Protocol'),
            description=_(u'A single protocol studying something like a biomarker.'),
            source=CatalogSource(object_provides=IProtocol.__identifier__)
        )
    )
    dexteritytextindexer.searchable('publications')
    publications = RelationList(
        title=_(u'Publications'),
        description=_(u'Publications that have been written discussing this object.'),
        default=[],
        required=False,
        value_type=RelationChoice(
            title=_(u'Publication'),
            description=_(u'A single publication talking about this object.'),
            source=CatalogSource(object_provides=IPublication.__identifier__)
        )
    )
    resources = RelationList(
        title=_(u'Resources'),
        description=_(u'Additional resources about this object.'),
        default=[],
        required=False,
        value_type=RelationChoice(
            title=_(u'Resource'),
            description=_(u'An additional resource about this object.'),
            source=CatalogSource(object_provides=IResource.__identifier__)
        )
    )
    datasets = RelationList(
        title=_(u'Datasets'),
        description=_(u'Datasets providing measured scientific bases for this biomarker.'),
        required=False,
        value_type=RelationChoice(
            title=_(u'Dataset'),
            description=_(u'A single dataset providing a measured scientific basis for this biomarker.'),
            source=CatalogSource(object_provides=IDataset.__identifier__)
        )
    )


class IBiomarker(IKnowledgeObject, IResearchedObject, IQualityAssuredObject):
    u'''An abstract biomarker.'''
    dexteritytextindexer.searchable('shortName')
    shortName = schema.TextLine(
        title=_(u'Short Name'),
        description=_(u'A shorter and preferred alias for the biomarker.'),
        required=False
    )
    dexteritytextindexer.searchable('hgncName')
    hgncName = schema.TextLine(
        title=_(u'HGNC Name'),
        description=_(u'The name assigned by the HUGO Gene Nomenclature Committee.'),
        required=False,
    )
    dexteritytextindexer.searchable('bmAliases')  # Why not a decorator? ¯\_(ツ)_/¯
    bmAliases = schema.List(
        title=_(u'Aliases'),
        description=_(u'Additional names by which the biomarker is known.'),
        required=False,
        value_type=schema.TextLine(
            title=_(u'Alias'),
            description=_(u'Another name for a biomarker.')
        )
    )
    indicatedBodySystems = schema.List(
        title=_(u'Indicated Organs'),
        description=_(u'Organs for which this biomarker is an indicator.'),
        required=False,
        value_type=schema.TextLine(
            title=_(u'Indicated Organ'),
            description=_(u'Organ for which this biomarker is an indicator.')
        )
    )
    collaborativeGroup = schema.List(
        title=_(u'Collaborative Groups'),
        description=_(u'Groups researching this biomarker.'),
        required=False,
        default=[],
        value_type=schema.TextLine(
            title=_(u'Collaborative Group'),
            description=_(u'Group researching this biomarker.')
        )
    )
    accessGroups = schema.List(
        title=_(u'Access Groups'),
        description=_(u'Groups that are allowed access to this biomarker.'),
        required=False,
        value_type=schema.TextLine(
            title=_(u'Access Group'),
            description=_(u'A single URI identifying a group that may access a biomarker.')
        )
    )
    geneName = schema.TextLine(
        title=_(u'Gene Symbol/Name'),
        description=_(u'The biomarker annotation that indicates gene symbol or name.'),
        required=False,
    )
    uniProtAC = schema.TextLine(
        title=_(u'Uniprot Accession'),
        description=_(u'The biomarker annotation that indicates the associated uniprot accession.'),
        required=False,
    )
    mutCount = schema.TextLine(
        title=_(u'Number of Mutation Sites'),
        description=_(u'The biomarker annotation that indicates the number of mutation sites.'),
        required=False,
    )
    pmidCount = schema.TextLine(
        title=_(u'Pubmed ID Count'),
        description=_(u'The biomarker annotation that indicates the number of associated pubmed ids.'),
        required=False,
    )
    cancerDOCount = schema.TextLine(
        title=_(u'CancerDO Count'),
        description=_(u'The biomarker annotation that indicates the CancerDO.'),
        required=False,
    )
    affProtFuncSiteCount = schema.TextLine(
        title=_(u'Affected Protein Function Site Count'),
        description=_(u'The biomarker annotation that indicates the number of affected protein function sites.'),
        required=False,
    )
    phases = schema.List(
        title=_(u'Phases'),
        description=_(u'Multiple phases of biomarker research of the contained body systems.'),
        required=False,
        value_type=schema.TextLine(
            title=_(u'Phase'),
            description=_(u'Single phase of biomarker research')
        )
    )


@implementer(IVocabularyFactory)
class PhasesVocabulary(object):
    u'''Vocabulary for biomarker phases'''
    def __call__(self, context):
        return generateVocabularyFromIndex('phases', context)


class IBiomarkerBodySystem(IKnowledgeObject, IResearchedObject, IPhasedObject, IQualityAssuredObject):
    u'''Research into a biomarker's effects on a single body system.'''
    performanceComment = schema.Text(
        title=_(u'Performance Comment'),
        description=_(u'A short summary of the biomarker performance with respect to a specific organ'),
        required=False
    )
    bodySystem = RelationChoice(
        title=_(u'Organ'),
        description=_(u'The organ for which the biomarker indicates diseases.'),
        required=False,
        source=CatalogSource(object_provides=IBodySystem.__identifier__)
    )
    cliaCertification = schema.Bool(
        title=_(u'CLIA Certification'),
        description=_(u'True if this biomarker has been certified by CLIA for this organ.'),
        required=False,
        default=False,
    )
    fdaCertification = schema.Bool(
        title=_(u'FDA Certification'),
        description=_(u'True if this biomarker has been certified by the FDA for this organ.'),
        required=False,
        default=False,
    )


class IBodySystemStudy(IKnowledgeObject, IResearchedObject):
    '''Study-specific information on a biomarker's effects on a single organ.'''
    protocol = RelationChoice(
        title=_(u'Study'),
        description=_(u'The study or protocol referenced by specific organ with regard to a biomarker.'),
        required=False,
        source=CatalogSource(object_provides=IProtocol.__identifier__)
    )
    decisionRule = schema.Text(
        title=_(u'Decision Rule'),
        description=_(u'Details about the decision rule for this body system study'),
        required=False,
    )


class IStudyStatistics(IKnowledgeObject):
    '''Statistician-friendly statistics.'''
    sensitivity = schema.TextLine(
        title=_(u'Sensitivity'),
        description=_(u'Proportion of actual positives that are correctly identified.'),
        required=False
    )
    specificity = schema.TextLine(
        title=_(u'Specificity'),
        description=_(u'Proportion of actual negatives that are correctly identified.'),
        required=False
    )
    npv = schema.TextLine(
        title=_(u'NPV'),
        description=_(u'Ratio of true negatives to combined true and false negatives.'),
        required=False
    )
    ppv = schema.TextLine(
        title=_(u'PPV'),
        description=_(u'Ratio of true positives to combined true and false positives.'),
        required=False
    )
    prevalence = schema.TextLine(
        title=_(u'Prevalence'),
        description=_(u'A percentage.'),
        required=False
    )
    details = schema.Text(
        title=_(u'Details'),
        description=_(u'Detailed notes about this set of statistics.'),
        required=False
    )
    specificAssayType = schema.Text(
        title=_(u'Specific Assay Type'),
        description=_(u'Information about the specific assay type used'),
        required=False
    )


def updateIndicatedBodySystems(context, event):
    if not IBiomarkerBodySystem.providedBy(context): return  # This should never happen but I'm defensive—er, paranoid.
    organName = context.id.capitalize()
    biomarker = context.aq_parent
    organs = list(biomarker.indicatedBodySystems if biomarker.indicatedBodySystems else [])
    if organName not in organs:
        organs.append(organName)
        organs.sort()
        biomarker.indicatedBodySystems = organs
        biomarker.reindexObject(idxs=['indicatedBodySystems'])


def updatePhases(context, event):
    if not IBiomarkerBodySystem.providedBy(context): return  # This should never happen but I'm defensive—er, paranoid.
    biomarker = context.aq_parent
    phases = set()
    for objID, biomarkerBodySystem in biomarker.contentItems():
        phase = biomarkerBodySystem.phase
        if phase is not None and phase:
            phases.add(phase)
    biomarker.phases = list(phases)
    biomarker.reindexObject(idxs=['phases'])


class BiomarkerView(BrowserView):
    def getType(self):
        raise NotImplementedError('subclass must impl')
    def viewable(self, section):
        context = aq_inner(self.context)
        # Accepted biomarkers are A-O-K no matter what section.
        if context.qaState == u'Accepted': return True
        # Certain sections are viewable for curated-but-not-yet-accepted biomarkers
        if context.qaState == u'Curated':
            canView = CURATED_SECTIONS.get(section, False)
            if canView: return True
        # Anonymous user?  Go away.
        mtool = plone.api.portal.get_tool('portal_membership')
        if mtool.isAnonymousUser(): return False
        # FIXME:
        # For purposes of the 2019-04-03 demo, logging in is enough. FIXME: figure out group LDAP mappings
        return True
        # Manager?  Welcome.
        member = mtool.getAuthenticatedMember()
        if 'Manager' in member.getRoles(): return True
        # Not a manager?  Check groups.
        gtool = plone.api.portal.get_tool('portal_groups')
        memberGroups = set([i.getGroupId() for i in gtool.getGroupsByUserId(member.getMemberId())])
        objectRoles = dict(context.get_local_roles())
        for groupName, roles in objectRoles.items():
            if u'Reader' in roles and groupName in memberGroups: return True
        return False
    def bodySystemsAvailable(self):
        return len(self.bodySystems()) > 0
    @memoize
    def bodySystems(self):
        context = aq_inner(self.context)
        mtool = plone.api.portal.get_tool('portal_membership')
        catalog = plone.api.portal.get_tool('portal_catalog')
        results = catalog(
            object_provides=IBiomarkerBodySystem.__identifier__,
            path=dict(query='/'.join(context.getPhysicalPath()), depth=1),
            sort_on='sortable_title'
        )
        results = [dict(
            name=i.Title,
            obj=i.getObject(),
            resources=[j.to_object for j in i.getObject().resources],
            viewable=i.getObject().qaState == u'Accepted' or not mtool.isAnonymousUser()
        ) for i in results]
        for result in results:
            resources = result['resources']
            resources.sort(lambda a, b: cmp(a.title, b.title))
        return results
    @memoize
    def studies(self, bodySystem):
        catalog = plone.api.portal.get_tool('portal_catalog')
        results = catalog(
            object_provides=IBodySystemStudy.__identifier__,
            path=dict(query='/'.join(bodySystem.getPhysicalPath()), depth=1),
            sort_on='sortable_title'
        )
        return [dict(name=i.Title, obj=i.getObject()) for i in results]
    @memoize
    def statistics(self, protocol):
        # TODO: implement this
        # def massage(value, deterministic=True):
        #     try:
        #         numeric = float(value)
        #     except (ValueError, TypeError):
        #         return u'ND' if deterministic else u'N/A' # ND = Not determined
        #     if numeric == 0.0:
        #         return u'N/A' # Not applicable
        #     return numeric
        # catalog = getToolByName(protocol, 'portal_catalog')
        # results = catalog(
        #     object_provides=IStudyStatistics.__identifier__,
        #     path=dict(query='/'.join(protocol.getPhysicalPath()), depth=1),
        #     sort_on='getObjPositionInParent'
        # )
        # return [dict(
        #     notes=i.getObject().details,
        #     sens=massage(i.getObject().sensitivity),
        #     spec=massage(i.getObject().specificity),
        #     npv=massage(i.getObject().npv, deterministic=False),
        #     ppv=massage(i.getObject().ppv, deterministic=False),
        #     prev=massage(i.getObject().prevalence, deterministic=False),
        # ) for i in results]
        return []
