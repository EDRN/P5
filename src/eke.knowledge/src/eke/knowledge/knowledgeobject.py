# encoding: utf-8


u'''EKE Knowledge: Knowledge Object'''

from collective import dexteritytextindexer
from eke.knowledge import _
from plone.supermodel import model
from zope import schema


class IKnowledgeObject(model.Schema):
    u'''Knowledge object.'''
    dexteritytextindexer.searchable('title')
    title = schema.TextLine(
        title=_(u'Title'),
        description=_(u'Name of this object.'),
        required=True,
    )
    dexteritytextindexer.searchable('description')
    description = schema.Text(
        title=_(u'Description'),
        description=_(u'A short summary of this object.'),
        required=False,
    )
    identifier = schema.TextLine(
        title=_(u'Identifier'),
        description=_(u'RDF Subject URI of this object'),
        required=True,
    )
