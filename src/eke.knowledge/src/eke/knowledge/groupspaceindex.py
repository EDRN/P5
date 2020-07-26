# encoding: utf-8


u'''EKE Knowledge: Group Space Index'''

from . import _
from Acquisition import aq_inner, aq_parent
from datetime import datetime
from plone.app.contenttypes.interfaces import IDocument, IEvent, IFile, IFolder, IImage
from plone.app.contenttypes.permissions import AddDocument, AddEvent, AddFile, AddFolder, AddImage
from plone.memoize.view import memoize
from plone.supermodel import model
from Products.Five import BrowserView
from zope import schema
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


class View(BrowserView):
    u'''View for a group space index'''
    def getAddableContent(self):
        '''Get the addable content types.  Subclasses can override.  Must return a mapping of type ID to
        a tuple of (permission name, portal type name, and true/false confusing flag).'''
        # This mapping goes from an addable content type ID (event, file, image, page) to a tuple identifying:
        # * The permission name to add an item of that type. Users must have that permission to add it.
        # * The name of the type according to the portal_types system.
        # * A flag indicating if such a type is confusing. Dan believes that users will find find adding
        #   plain old wiki-style HTML pages and images upsetting. So we automatically hide such confusing
        #   buttons. The tyranny of closed Micro$oft formats continues.
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
        catalog = plone.api.portal.get_tool('portal_catalog')
        results = catalog(
            object_provides=IEvent.__identifier__,
            path=dict(query='/'.join(context.getPhysicalPath()), depth=1),
            sort_on='start',
            sort_order='reverse',
            **criteria)
        return [dict(title=i.Title, description=i.Description, start=i.start, url=i.getURL()) for i in results]
    @memoize
    def membersColumns(self):
        members = aq_inner(self.context).members
        members.sort(lambda a, b: cmp(a.to_object.title, b.to_object.title))
        half = len(members) / 2 + 1
        left, right = members[:half], members[half:]
        return left, right
    def showNewButton(self, buttonType):
        addableContent = self.getAddableContent()
        if buttonType not in addableContent: return False
        context = aq_parent(aq_inner(self.context))
        mtool = plone.api.portal.get_tool('portal_membership')
        perm = mtool.checkPermission(addableContent[buttonType][0], context)
        return perm and not addableContent[buttonType][2]
    def newButtonLink(self, buttonType):
        addableContent = self.getAddableContent()
        return aq_parent(aq_inner(self.context)).absolute_url() + '/++add++' + addableContent[buttonType][1]
    def haveDocument(self):
        return len(self.documents()) > 0
    @memoize
    def documents(self):
        context = aq_parent(aq_inner(self.context))
        results = context.restrictedTraverse('@@contentlisting')(
            object_provides=[i.__identifier__ for i in (IDocument, IImage, IFile, IFolder)],
            sort_on='modified',
            sort_order='reverse'
        )
        # For some reason Highlights are being returned in the results, even though they don't provide any of the interfaces.
        # CA-1431: also events
        results = [i for i in results if i.portal_type not in ('Highlight', 'Group Event')]
        return results
