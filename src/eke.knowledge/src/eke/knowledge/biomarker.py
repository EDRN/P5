# encoding: utf-8

u'''Biomarkers'''

from . import _
from .bodysystem import IBodySystem
from .knowledgeobject import IKnowledgeObject
from .protocol import IProtocol
from .publication import IPublication
from five import grok
from plone.app.vocabularies.catalog import CatalogSource
from z3c.relationfield.schema import RelationChoice, RelationList
from zope import schema
from zope.interface import Interface


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
            source=CatalogSource(object_provides=IKnowledgeObject.__identifier__)
        )
    )
    datasets = schema.List(
        title=_(u'Datasets'),
        description=_(u'Datasets providing measured scientific bases for this biomarker.'),
        required=False,
        value_type=schema.TextLine(
            title=_(u'Dataset'),
            description=_(u'Dataset providing a measured scientific basis for this biomarker.'),
        )
    )


class IBiomarker(IKnowledgeObject, IResearchedObject, IQualityAssuredObject):
    u'''An abstract biomarker.'''
    shortName = schema.TextLine(
        title=_(u'Short Name'),
        description=_(u'A shorter and preferred alias for the biomarker.'),
        required=False
    )
    hgncName = schema.TextLine(
        title=_(u'HGNC Name'),
        description=_(u'The name assigned by the HUGO Gene Nomenclature Committee.'),
        required=False,
    )
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
    accessGroups = schema.List(
        title=_(u'Access Groups'),
        description=_(u'Groups that are allowed access to this biomarker.'),
        required=False,
        value_type=schema.TextLine(
            title=_(u'Access Group'),
            description=_(u'A single URI identifying a group that may access a biomarker.')
        )
    )
    biomarkerKind = schema.TextLine(
        title=_(u'Kind'),
        description=_(u'What kind of biomarker.'),
        required=False,
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


class IBiomarkerPanel(IBiomarker):
    u'''A panel of biomarkers that itself behaves as a single (yet composite) biomarker.'''
    members = RelationList(
        title=_(u'Member Markers'),
        description=_(u'Biomarkers that are a part of this panel'),
        required=False,
        value_type=RelationChoice(
            title=_(u'Member Marker'),
            description=_(u"A biomarker that's part of a panel."),
            source=CatalogSource(IBiomarker.__identifier__)
        )
    )


class IElementalBiomarker(IBiomarker):
    u'''A single, actual biomarker.'''
    biomarkerType = schema.TextLine(
        title=_(u'Biomarker Type'),
        description=_(u'The general category, kind, or class of this biomarker.'),
        required=False
    )


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
    sensitivity = schema.Float(
        title=_(u'Sensitivity'),
        description=_(u'Proportion of actual positives that are correctly identified.'),
        required=False
    )
    specificity = schema.Float(
        title=_(u'Specificity'),
        description=_(u'Proportion of actual negatives that are correctly identified.'),
        required=False
    )
    npv = schema.Float(
        title=_(u'NPV'),
        description=_(u'Ratio of true negatives to combined true and false negatives.'),
        required=False
    )
    ppv = schema.Float(
        title=_(u'PPV'),
        description=_(u'Ratio of true positives to combined true and false positives.'),
        required=False
    )
    prevalence = schema.Float(
        title=_(u'Prevalence'),
        description=_(u'A percentage.'),
        required=False
    )
    details = schema.TextLine(
        title=_(u'Details'),
        description=_(u'Detailed notes about this set of statistics.'),
        required=False
    )
    specificAssayType = schema.Text(
        title=_(u'Specific Assay Type'),
        description=_(u'Information about the specific assay type used'),
        required=False
    )
