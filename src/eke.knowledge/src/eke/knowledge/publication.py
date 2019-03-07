# encoding: utf-8

from . import _, dublincore
from knowledgeobject import IKnowledgeObject
from zope import schema


class IPublication(IKnowledgeObject):
    u'''Something published.'''
    authors = schema.List(
        title=_(u'Authors'),
        description=_(u'Creators of the publication.'),
        required=False,
        value_type=schema.TextLine(
            title=_(u'Author'),
            description=_(u'A creator of a publication.'),
            required=False
        )
    )
    issue = schema.TextLine(
        title=_(u'Issue'),
        description=_(u'In what issue the publication appeared.'),
        required=False,
    )
    volume = schema.TextLine(
        title=_(u'Volume'),
        description=_(u'In what volume the issue appeared in which the publication appeared.'),
        required=False,
    )
    journal = schema.TextLine(
        title=_(u'Journal'),
        description=_(u'Name of the journal in which the publication appeared.'),
        required=False,
    )
    pubMedID = schema.TextLine(
        title=_(u'PubMed ID'),
        description=_(u'PubMed identifier for the publication.'),
        required=False,
    )
    month = schema.TextLine(
        title=_(u'Month'),
        description=_(u'Month of publication.'),
        required=False,
    )
    year = schema.TextLine(
        title=_(u'Year'),
        description=_(u'Year of publication.'),
        required=False,
    )
    pubURL = schema.TextLine(
        title=_(u'URL'),
        description=_(u'Location of the publication.'),
        required=False,
    )


IPublication.setTaggedValue('predicates', {
    dublincore.TITLE_URI: ('title', False),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#abstract': ('description', False),
    dublincore.AUTHOR_URI: ('authors', False),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#issue': ('issue', False),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#volume': ('volume', False),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#journal': ('journal', False),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#pmid': ('pubMedID', False),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#year': ('year', False),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#month': ('month', False),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#pubURL': ('pubURL', False)
})
IPublication.setTaggedValue('fti', 'eke.knowledge.publication')
IPublication.setTaggedValue('typeURI', u'http://edrn.nci.nih.gov/rdf/types.rdf#Publication')
