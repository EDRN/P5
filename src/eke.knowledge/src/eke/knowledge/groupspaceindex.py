# encoding: utf-8


u'''EKE Knowledge: Group Space Index'''

from Acquisition import aq_inner, aq_parent
from eke.knowledge import _
from five import grok
from plone.app.contenttypes.permissions import AddDocument, AddEvent, AddFile, AddFolder, AddImage
from plone.memoize.view import memoize
from plone.supermodel import model
from zope import schema
from datetime import datetime
from plone.app.vocabularies.catalog import CatalogSource
from z3c.relationfield.schema import RelationChoice, RelationList
from .person import IPerson
import plone.api


# Number of top items to show. 3 is a good number.
_top = 3


class IGroupSpaceIndex(model.Schema):
    u'''Index page for a group space folder.'''
    title = schema.TextLine(
        title=_(u'Title'),
        description=_(u'Descriptive name of this index page.'),
        required=True,
    )
    description = schema.Text(
        title=_(u'Description'),
        description=_(u'A short summary of this index page.'),
        required=False,
    )
    chair = RelationChoice(
        title=_(u'Chair'),
        description=_(u'The person in charge of this group.'),
        required=False,
        source=CatalogSource(object_provides=IPerson.__identifier__)
    )
    coChair = RelationChoice(
        title=_(u'Co-Chair'),
        description=_(u'The assistant to the person in charge of this grou.'),
        required=False,
        source=CatalogSource(object_provides=IPerson.__identifier__)
    )
    members = RelationList(
        title=_(u'Members'),
        description=_(u'Members of this group.'),
        default=[],
        required=False,
        value_type=RelationChoice(
            title=_(u'Member'),
            description=_(u'A member of this group.'),
            source=CatalogSource(object_provides=IPerson.__identifier__)
        )
    )


class View(grok.View):
    u'''View for a group space index'''
    grok.context(IGroupSpaceIndex)
    def getAddableContent(self):
        '''Get the addable content types.  Subclasses can override.  Must return a mapping of type ID to
        a tuple of (permission name, portal type name, and true/false confusing flag).'''
        # This mapping goes from an addable content type ID (event, file, image, page) to a tuple identifying:
        # * The permission name to add an item of that type. Users must have that permission to add it.
        # * The name of the type according to the portal_types system.
        # * A flag indicating if such a type is confusing. Dan believes that users will find find adding
        #   plain old wiki-style HTML pages and images upsetting. So we automatically hide such confusing
        #   buttons. The tyranny of closed Micro$oft formats continues.
        # BTW: Why aren't these permission names defined as constants somewhere in ATContentTypes?
        return {
            # Add type  Permission    Type name   Confusing?
            'event':    (AddEvent,    'Event',    False),
            'file':     (AddFile,     'File',     False),
            'image':    (AddImage,    'Image',    True),
            'page':     (AddDocument, 'Document', True),
            'folder':   (AddFolder,   'Folder',   False),
        }
    def numTops(self):
        return _top
    def facebookURL(self):
        context = aq_parent(aq_inner(self.context))
        return u'https://facebook.com/sharer.php?' + urllib.urlencode(dict(t=context.title, u=context.absolute_url()))
    def twitterURL(self):
        context = aq_parent(aq_inner(self.context))
        return u'https://twitter.com/intent/tweet?url=' + urllib.urlencode(dict(text=context.title, url=context.absolute_url()))
    @memoize
    def topEvents(self):
        return self.currentEvents()[0:self.numTops()]
    @memoize
    def numEvents(self):
        return len(self.currentEvents())
    def haveEvents(self):
        return len(self.currentEvents()) > 0
    def havePastEvents(self):
        return len(self.pastEvents()) > 0
    @memoize
    def currentEvents(self):
        return self._getEvents(end={'query': datetime.utcnow(), 'range': 'min'})
    @memoize
    def pastEvents(self):
        return self._getEvents(end={'query': datetime.utcnow(), 'range': 'max'})
    def _getEvents(self, **criteria):
        context = aq_parent(aq_inner(self.context))
        catalog = getToolByName(context, 'portal_catalog')
        results = catalog(
            object_provides=IATEvent.__identifier__,
            path=dict(query='/'.join(context.getPhysicalPath()), depth=1),
            sort_on='start',
            sort_order='reverse',
            **criteria)
        return [dict(title=i.Title, description=i.Description, start=i.start, url=i.getURL()) for i in results]
    @memoize
    def membersColumns(self):
        members = aq_inner(self.context).members
        members.sort(lambda a, b: cmp(a.to_object.title, b.to_object.title))
        half = len(members)/2 + 1
        left, right = members[:half], members[half:]
        return left, right
    def showNewButton(self, buttonType):
        addableContent = self.getAddableContent()
        if buttonType not in addableContent: return False
        context = aq_parent(aq_inner(self.context))
        mtool = getToolByName(context, 'portal_membership')
        perm = mtool.checkPermission(addableContent[buttonType][0], context)
        return perm and not addableContent[buttonType][2]
    def newButtonLink(self, buttonType):
        addableContent = self.getAddableContent()
        return aq_parent(aq_inner(self.context)).absolute_url() + '/createObject?type_name=' + addableContent[buttonType][1]
    def haveDocument(self):
        return len(self.documents()) > 0
    @memoize
    def documents(self):
        context = aq_parent(aq_inner(self.context))
        contentFilter = dict(
            object_provides=[i.__identifier__ for i in (IATDocument, IATImage, IATFile, IATFolder)],
            sort_on='modified',
            sort_order='reverse'
        )
        results = context.getFolderContents(contentFilter=contentFilter)
        # For some reason Highlights are being returned in the results, even though they don't provide any of the interfaces.
        # CA-1431: also events
        results = [i for i in results if i.portal_type not in ('Highlight', 'Group Event')]
        return results
