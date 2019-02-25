# encoding: utf-8


u'''EKE Knowledge: Knowledge Object'''

from eke.knowledge import _
from plone.supermodel import model
from zope import schema


class IKnowledgeObject(model.Schema):
    u'''Knowledge object.'''
    title = schema.TextLine(
        title=_(u'Title'),
        description=_(u'Name of this object.'),
        required=True,
    )
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
