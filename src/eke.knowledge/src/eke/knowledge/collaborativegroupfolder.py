# encoding: utf-8


u'''EKE Knowledge: Collaborative Group Folder'''

from .groupspacefolder import IGroupSpaceFolder
from five import grok
from plone.dexterity.utils import createContentInContainer
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes, ENABLED
from zope.container.interfaces import IObjectAddedEvent


class ICollaborativeGroupFolder(IGroupSpaceFolder):
    u'''Folder for an individual collaborative group to hold their stuff.'''


@grok.subscribe(ICollaborativeGroupFolder, IObjectAddedEvent)
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
