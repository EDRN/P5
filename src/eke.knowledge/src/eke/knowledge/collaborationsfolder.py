# encoding: utf-8


u'''EKE Knowledge: Collaborations Folder'''

from eke.knowledge import _
from five import grok
from plone.supermodel import model
from zope import schema
import plone.api


class ICollaborationsFolder(model.Schema):
    u'''Collaborations folder.'''
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
