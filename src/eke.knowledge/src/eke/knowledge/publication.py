# encoding: utf-8

# from .person import IPerson  # Cannot import due to circulal dependency; using generated name in view class below

from . import _, dublincore
from Acquisition import aq_inner
from collective import dexteritytextindexer
from knowledgeobject import IKnowledgeObject
from plone.app.textfield import RichText
from plone.memoize.view import memoize
from Products.Five import BrowserView
from zope import schema
import plone.api, cgi


class IPublication(IKnowledgeObject):
    u'''Something published.'''
    abstract = RichText(
        title=_(u'Abstract'),
        description=_(u'A summary of the content of this publication.'),
        required=False,
    )
    dexteritytextindexer.searchable('authors')
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
    # Note we're treating ``siteID`` as a plain literal field even though in RDF
    # it's a reference to another object (a Site object).  This lets the person.py
    # view find publications by looking up its containing Site's Identifier on
    # the siteID index.
    siteID = schema.TextLine(
        title=_(u'Site ID'),
        description=_(u'DMCC-assigned identifier for the site that wrote this publication.'),
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
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#pubURL': ('pubURL', False),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#site': ('siteID', False)
})
IPublication.setTaggedValue('fti', 'eke.knowledge.publication')
IPublication.setTaggedValue('typeURI', u'http://edrn.nci.nih.gov/rdf/types.rdf#Publication')


class View(BrowserView):
    def haveAuthors(self):
        context = aq_inner(self.context)
        return len(context.authors) > 0
    @memoize
    def authors(self):
        context, catalog = aq_inner(self.context), plone.api.portal.get_tool('portal_catalog')
        authorNames = list(context.authors)
        authorNames.sort()
        authors = []
        for authorName in authorNames:
            space = authorName.find(u' ')
            surname = authorName[0:space] if space > 0 else authorName
            results = catalog(object_provides='eke.knowledge.person.IPerson', Title=surname)
            if len(results) == 0:
                authors.append(cgi.escape(authorName))
            else:
                authors.append(u'<a href="{}">{}</a>'.format(results[0].getURL(), cgi.escape(authorName)))
        return u', '.join(authors)
    @memoize
    def appearance(self):
        context = aq_inner(self.context)
        appearances = []
        if context.journal: appearances.append(context.journal)
        if context.year: appearances.append(context.year)
        if context.month: appearances.append(context.month)
        if context.volume: appearances.append(context.volume)
        appearances = u', '.join(appearances)
        if context.issue: appearances += u' ({})'.format(cgi.escape(context.issue))
        return appearances
