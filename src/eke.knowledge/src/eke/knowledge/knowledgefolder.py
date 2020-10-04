# encoding: utf-8


u'''EKE Knowledge: Knowledge Folder'''

from . import _
from Acquisition import aq_inner
from plone.supermodel import model
from Products.Five import BrowserView
from zope import schema
import plone.api


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
    rdfDataSources = schema.List(
        title=_(u'RDF Data Sources'),
        description=_(u'URLs to sources of Resource Description Format (RDF) data.'),
        required=False,
        # ❌ Plone 5.2.2 problem; this hsould be schema.URI, not schema.TextLine, but causes a stack
        # trace on edits; see: https://community.plone.org/t/plone-5-2-2-regression-with-schema-uri-based-fields/
        value_type=schema.TextLine(
            title=_(u'RDF Data Source'),
            description=_(u'URL to a source of Resource Description Format data that mandates the contents of this folder.'),
            required=False,
        )
    )
    ingestEnabled = schema.Bool(
        title=_(u'Ingest Enabled'),
        description=_(u'True if this folder should update its contents, false otherwise.'),
        required=False
    )


class KnowledgeFolderView(BrowserView):
    def contents(self):
        context = aq_inner(self.context)
        catalog = plone.api.portal.get_tool('portal_catalog')
        return catalog(path={'query': '/'.join(context.getPhysicalPath()), 'depth': 1}, sort_on='sortable_title')
    def isManager(self):
        context = aq_inner(self.context)
        membership = plone.api.portal.get_tool('portal_membership')
        return membership.checkPermission('Manage Portal', context)
