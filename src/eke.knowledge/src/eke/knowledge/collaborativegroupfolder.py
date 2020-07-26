# encoding: utf-8


u'''EKE Knowledge: Collaborative Group Folder'''

from .dublincore import TITLE_URI, DESCRIPTION_URI
from .groupspacefolder import IGroupSpaceFolder
from plone.dexterity.utils import createContentInContainer
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes, ENABLED


class ICollaborativeGroupFolder(IGroupSpaceFolder):
    u'''Folder for an individual collaborative group to hold their stuff.'''


def setupCollaborativeGroupFolder(folder, event):
    if not ICollaborativeGroupFolder.providedBy(folder):
        # This is in case the group space superclass' event fires. We want this only on
        # actual ICollaborativeGroupFolders, not IGroupSpaceFolders.
        return
    # Add index page
    if 'index_html' not in folder.keys():
        index = createContentInContainer(
            folder,
            'eke.knowledge.collaborativegroupindex',
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
    try:
        addableTypes.remove('eke.knowledge.collaborativegroupindex')
        i.setImmediatelyAddableTypes(addableTypes)
    except ValueError:
        pass


ICollaborativeGroupFolder.setTaggedValue('predicates', {
    TITLE_URI: ('title', False),
    DESCRIPTION_URI: ('description', False),
    u'http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#chair': ('chair', True),
    u'http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#coChair': ('coChair', True),
    u'http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#member': ('members', True),
})
ICollaborativeGroupFolder.setTaggedValue('fti', 'eke.knowledge.collaborativegroupfolder')
ICollaborativeGroupFolder.setTaggedValue('typeURI', u'http://edrn.nci.nih.gov/rdf/types.rdf#Committee')
