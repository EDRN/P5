# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from . import _
from zope import schema
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IEkeKnowledgeLayer(IDefaultBrowserLayer):
    u'''Marker interface that defines a browser layer.'''


class IPanel(Interface):
    u'''Schema for the EKE knowledge control panel.'''
    ingestEnabled = schema.Bool(
        title=_(u'Enable Ingest'),
        description=_(u"Globally enable (or disable) RDF ingest."),
        required=False,
    )
    ingestStart = schema.Datetime(
        title=_(u'Start Time'),
        description=_(u"When set this tells the time an active ingest started. No need to set this, it's automatic."),
        required=False,
    )
    objects = schema.List(
        title=_(u'Ingest Objects'),
        description=_(u'Paths to objects to ingest.'),
        required=False,
        value_type=schema.TextLine(
            title=_(u'Object'),
            description=_(u'Path to an object to ingest.')
        )
    )


class IIngestor(Interface):
    u'''Adapt objects so they can ingest RDF data'''
    def ingest():
        u'''Ingest RDF and return an IngestConsequences object.'''
