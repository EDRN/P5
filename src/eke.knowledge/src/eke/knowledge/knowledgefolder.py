# encoding: utf-8


u'''EKE Knowledge: Knowledge Folder'''

from eke.knowledge import _
from plone.supermodel import model
from zope import schema


class IKnowledgeFolder(model.Schema):
    u'''Knowledge folder.'''
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
    rdfDataSource = schema.URI(
        title=_(u'RDF Data Source'),
        description=_(u'URL to a source of Resource Description Format data that mandates the contents of this folder.'),
        required=False,
    )
    ingestEnabled = schema.Bool(
        title=_(u'Ingest Enabled'),
        description=_(u'True if this folder should update its contents, false otherwise.'),
        required=False
    )
