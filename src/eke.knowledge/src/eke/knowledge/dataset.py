# encoding: utf-8

# from plone.formwidget.contenttree import ObjPathSourceBinder
# No longer for Plone 5?
from . import _
from .bodysystem import IBodySystem
from .dublincore import TITLE_URI
from .person import IPerson
from .protocol import IProtocol
from .site import ISite
from Acquisition import aq_inner
from collective import dexteritytextindexer
from five import grok
from knowledgeobject import IKnowledgeObject
from plone.app.vocabularies.catalog import CatalogSource
from plone.memoize.view import memoize
from z3c.relationfield.schema import RelationChoice, RelationList
from zope import schema
from zope.interface import Interface
import plone.api


class IDataset(IKnowledgeObject):
    '''Dataset.'''
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
    bodySystem = RelationChoice(
        title=_(u'Body System'),
        description=_(u'About what body system (such as an organ) this science data is'),
        required=False,
        source=CatalogSource(object_provides=IBodySystem.__identifier__)
    )
    bodySystemName = schema.TextLine(
        title=_(u'Body System Name'),
        description=_(u'The name of the body system (such as an organ).'),
        required=False,
    )
    protocolName = schema.TextLine(
        title=_(u'Protocol Name'),
        description=_(u'The name of the protocol or study that produced this data.'),
        required=False,
    )
    dexteritytextindexer.searchable('investigator')
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
    u'urn:edrn:DataCustodian': ('custodian', False),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#protocol': ('protocol', True),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#site': ('sites', True),
    u'urn:edrn:Author': ('authors', False),
    u'urn:edrn:GrantSupport': ('grantSupport', False),
    u'urn:edrn:ResearchSupport': ('researchSupport', False),
    u'urn:edrn:DataDisclaimer': ('dataDisclaimer', False),
    u'urn:edrn:StudyBackground': ('studyBackground', False),
    u'urn:edrn:StudyMethods': ('studyMethods', False),
    u'urn:edrn:StudyResults': ('studyResults', False),
    u'urn:edrn:StudyConclusion': ('studyConclusion', False),
    u'urn:edrn:Date': ('dataUpdateDate', False),
    u'urn:edrn:CollaborativeGroup': ('collaborativeGroup', False),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#organ': ('bodySystem', True)
})
IDataset.setTaggedValue('fti', 'eke.knowledge.dataset')
IDataset.setTaggedValue('typeURI', u'http://edrn.nci.nih.gov/rdf/types.rdf#Dataset')


class View(grok.View):
    grok.context(IDataset)
    grok.require('zope2.View')
