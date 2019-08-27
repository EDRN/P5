# encoding: utf-8


u'''EKE Knowledge: Group Space Folder'''

from .dublincore import TITLE_URI, DESCRIPTION_URI
from .knowledgeobject import IKnowledgeObject
from .person import IPerson
from eke.knowledge import _
from five import grok
from plone.app.vocabularies.catalog import CatalogSource
from plone.dexterity.utils import createContentInContainer
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes, ENABLED
from z3c.relationfield.schema import RelationChoice, RelationList
from zope import schema
from zope.container.interfaces import IObjectAddedEvent


class IGroupSpaceFolder(IKnowledgeObject):
    u'''Group space folder.'''
    chair = RelationChoice(
        title=_(u'Chair'),
        description=_(u'The person in charge of this group.'),
        required=False,
        source=CatalogSource(object_provides=IPerson.__identifier__)
    )
    coChair = RelationChoice(
        title=_(u'Co-Chair'),
        description=_(u'The assistant to the person in charge of this group.'),
        required=False,
        source=CatalogSource(object_provides=IPerson.__identifier__)
    )
    members = RelationList(
        title=_(u'Members'),
        description=_(u'Members of this group.'),
        default=[],
        required=False,
        value_type=RelationChoice(
            title=_(u'Member'),
            description=_(u'A member of this group.'),
            source=CatalogSource(object_provides=IPerson.__identifier__)
        )
    )


@grok.subscribe(IGroupSpaceFolder, IObjectAddedEvent)
def setupGroupSpaceFolder(folder, event):
    if not IGroupSpaceFolder.providedBy(folder): return  # This should never happen but I'm defensive—er, paranoid.
    try:
        # Add index page
        if 'index_html' not in folder.keys():
            index = createContentInContainer(
                folder,
                'eke.knowledge.groupspaceindex',
                id='index_html',
                title=folder.title,
                description=folder.description
            )
            index.reindexObject()
            folder.setDefaultPage('index_html')
        # Make index page not easily addable
        i = ISelectableConstrainTypes(folder)
        i.setConstrainTypesMode(ENABLED)
        addableTypes = i.getImmediatelyAddableTypes()
        addableTypes.remove('eke.knowledge.groupspaceindex')
        i.setImmediatelyAddableTypes(addableTypes)
    except ValueError:
        # A cleaner way would be to use a tagged value on the interface class
        # to determine what the index page type should be, but there's only one
        # subclass
        pass


IGroupSpaceFolder.setTaggedValue('predicates', {
    TITLE_URI: ('title', False),
    DESCRIPTION_URI: ('description', False),
    u'http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#chair': ('chair', True),
    u'http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#coChair': ('coChair', True),
    u'http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#member': ('members', True),
})
IGroupSpaceFolder.setTaggedValue('fti', 'eke.knowledge.groupspacefolder')
IGroupSpaceFolder.setTaggedValue('typeURI', u'http://edrn.nci.nih.gov/rdf/types.rdf#Committee')
