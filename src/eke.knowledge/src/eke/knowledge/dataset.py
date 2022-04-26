# encoding: utf-8

# from plone.formwidget.contenttree import ObjPathSourceBinder
# No longer for Plone 5?

from . import _
from .dublincore import TITLE_URI
from .person import IPerson
from .protocol import IProtocol
from .site import ISite
from collective import dexteritytextindexer
from knowledgeobject import IKnowledgeObject
from plone.app.vocabularies.catalog import CatalogSource
from z3c.relationfield.schema import RelationChoice, RelationList
from zope import schema


class IDataset(IKnowledgeObject):
    '''Dataset; actually a LabCAS Collection, not a dataset.'''
    dexteritytextindexer.searchable('custodian')
    custodian = schema.TextLine(
        title=_(u'Custodian'),
        description=_(u'The caretaker of this science data.'),
        required=False,
    )
    protocol = RelationChoice(
        title=_(u'Protocol'),
        description=_(u'The protocol or study that produced this science data.'),
        required=False,
        source=CatalogSource(object_provides=IProtocol.__identifier__)
    )
    sites = RelationList(
        title=_(u'Sites'),
        description=_(u'EDRN sites that contributed to this science data.'),
        default=[],
        required=False,
        value_type=RelationChoice(
            title=_(u'Site'),
            description=_(u'Single EDRN site that contributed to this sceince data.'),
            source=CatalogSource(object_provides=ISite.__identifier__)
        )
    )
    authors = schema.List(
        title=_(u'Authors'),
        description=_(u'People who created this data.'),
        required=False,
        value_type=schema.TextLine(title=_(u'Author'), description=_(u'A single author who helped create this data.'))
    )
    grantSupport = schema.List(
        title=_(u'Grant Support'),
        description=_(u'Grants that are supporting this science data.'),
        required=False,
        value_type=schema.TextLine(title=_(u'Supporting Grant'), description=_(u'A single grant supporting this science data.'))
    )
    researchSupport = schema.List(
        title=_(u'Research Support'),
        description=_(u'Research that supported this science data.'),
        required=False,
        value_type=schema.TextLine(
            title=_(u'Research'),
            description=_(u'A single instance of research that supported this science data.'))
    )
    dataDisclaimer = schema.Text(
        title=_(u'Data Disclaimer'),
        description=_(u'A legal license, warranty, indemnity, and release detailing the acceptable use of this science data.'),
        required=False,
    )
    studyBackground = schema.Text(
        title=_(u'Study Background'),
        description=_(u'Background information that would be useful to know before using this science data.'),
        required=False,
    )
    studyMethods = schema.Text(
        title=_(u'Study Methods'),
        description=_(u'Various methods that may be employed in the study of this science data.'),
        required=False,
    )
    studyResults = schema.Text(
        title=_(u'Study Results'),
        description=_(u'Results that come from studying this science data.'),
        required=False,
    )
    studyConclusion = schema.Text(
        title=_(u'Study Conclusion'),
        description=_(u'The conclusion that may be drawn from analyzing this science data.'),
        required=False,
    )
    dataUpdateDate = schema.TextLine(
        title=_(u'Date'),
        description=_(u'Date this data was last updated.'),
        required=False,
    )
    collaborativeGroup = schema.TextLine(
        title=_(u'Collaborative Group'),
        description=_(u'Which group collaborated to help make this science data.'),
        required=False,
    )
    bodySystemName = schema.List(
        title=_(u'Body System Names'),
        description=_(u'The names of the body system (such as organs).'),
        required=False,
        value_type=schema.TextLine(title=_(u'Body System Name'), description=_(u'Name of a single body system (organ).'))
    )
    protocolName = schema.TextLine(
        title=_(u'Protocol Name'),
        description=_(u'The name of the protocol or study that produced this data.'),
        required=False,
    )
    dexteritytextindexer.searchable('investigatorName')
    investigatorName = schema.TextLine(
        title=_(u'Investigator Name'),
        description=_(u"Name of the principal investigator of this data if the protocol doesn't otherwise indicate"),
        required=False,
    )
    investigator = RelationChoice(
        title=_(u'Investigator'),
        description=_(u'Principal investigator investigating this data.'),
        source=CatalogSource(object_provides=IPerson.__identifier__)
    )
    # collaborativeGroupUID = schema.TextLine(
    #     title=_(u'Collaborative Group UID'),
    #     description=_(u'Unique ID of the collaborative group that produced this dataset.'),
    #     required=False,
    # )


IDataset.setTaggedValue('predicates', {
    TITLE_URI: ('title', False),
    u'urn:edrn:predicates:protocol': ('protocol', True),
    u'urn:edrn:predicates:pi': ('investigatorName', False),
    u'urn:edrn:predicates:collaborativeGroup': ('collaborativeGroup', False),
    u'urn:edrn:predicates:organ': ('bodySystemName', False)

    # These fields no longer appear in the LabCAS RDF:
    # u'urn:edrn:DataCustodian': ('custodian', False),
    # u'http://edrn.nci.nih.gov/rdf/schema.rdf#site': ('sites', True),
    # u'urn:edrn:Author': ('authors', False),
    # u'urn:edrn:GrantSupport': ('grantSupport', False),
    # u'urn:edrn:ResearchSupport': ('researchSupport', False),
    # u'urn:edrn:DataDisclaimer': ('dataDisclaimer', False),
    # u'urn:edrn:StudyBackground': ('studyBackground', False),
    # u'urn:edrn:StudyMethods': ('studyMethods', False),
    # u'urn:edrn:StudyResults': ('studyResults', False),
    # u'urn:edrn:StudyConclusion': ('studyConclusion', False),
    # u'urn:edrn:Date': ('dataUpdateDate', False),
})
IDataset.setTaggedValue('fti', 'eke.knowledge.dataset')
IDataset.setTaggedValue('typeURI', u'urn:edrn:types:labcas:collection')
