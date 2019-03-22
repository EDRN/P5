# encoding: utf-8


u'''EKE Knowledge: Group Space Folder'''

from eke.knowledge import _
from five import grok
from plone.dexterity.utils import createContentInContainer
from plone.supermodel import model
from zope import schema
from zope.container.interfaces import IObjectAddedEvent


class IGroupSpaceFolder(model.Schema):
    u'''Group space folder.'''
    title = schema.TextLine(
        title=_(u'Title'),
        description=_(u'Descriptive name of this folder.'),
        required=True,
    )
    description = schema.Text(
        title=_(u'Description'),
        description=_(u'A short summary of this folder.'),
        required=False,
    )


@grok.subscribe(IGroupSpaceFolder, IObjectAddedEvent)
def createIndex(folder, event):
    if not IGroupSpaceFolder.providedBy(folder): return  # This should never happen but I'm defensive—er, paranoid.
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
