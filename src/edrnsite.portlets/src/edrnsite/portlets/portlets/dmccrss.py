# -*- coding: utf-8 -*-

u'''DMCC RSS Portlet'''

from edrnsite.portlets import _
from plone.app.portlets.portlets import base
from plone.app.portlets.portlets.rss import IFeed, RSSFeed
from plone.portlets.interfaces import IPortletDataProvider
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from zope import schema
from zope.interface import implementer
import logging


DEFAULT_URL = u'http://www.compass.fhcrc.org/edrnnci/rss.asp?t=Announcement&type=1&web=8&d=03/01/05&p=&num=15'
DEFAULT_TIMEOUT = 100
DEFAULT_COUNT = 2
DEFAULT_TITLE = u'DMCC News'

FEED_DATA = {}  # Mapping from url: to (date, title, url, itemlist)

_logger = logging.getLogger(__name__)


class IDMCCFeed(IFeed):
    u'''A feed from the DMCC which doesn't really utilize RSS all that well'''
    pass


@implementer(IDMCCFeed)
class DMCCRSSFeed(RSSFeed):
    u'''Silly RSS feed from the DMCC'''
    def __init__(self, url=None, timeout=None):
        url = DEFAULT_URL if url is None else url
        timeout = DEFAULT_TIMEOUT if timeout is None else timeout
        super(DMCCRSSFeed, self).__init__(url, timeout)


class IDMCCRSSPortlet(IPortletDataProvider):
    portlet_title = schema.TextLine(
        title=_(u'Title'),
        description=_(u'Title of the portlet; defaults to "{}".'.format(DEFAULT_TITLE)),
        required=False,
        default=DEFAULT_TITLE,
    )
    count = schema.Int(
        title=_(u'Number of items to display'),
        description=_(u'How many news items to list.'),
        required=True,
        default=2
    )
    url = schema.TextLine(
        title=_(u'RSS URL'),
        description=_(u'Link of the DMCC RSS feed; defaults to announcements.'),
        required=True,
        default=DEFAULT_URL
    )
    timeout = schema.Int(
        title=_(u'Refresh Timeout'),
        description=_(u'Time in minutes when feed is considered expired and fresh data retrieved.'),
        required=True,
        default=DEFAULT_TIMEOUT
    )


@implementer(IDMCCRSSPortlet)
class Assignment(base.Assignment):
    portlet_title = u''
    @property
    def title(self):
        feed = FEED_DATA.get(self.data.url, None)
        if feed is None:
            return u'RSS: ' + self.url[:20]
        else:
            return u'RSS: ' + feed.title[:20]
    def __init__(self, portlet_title=DEFAULT_TITLE, count=DEFAULT_COUNT, url=DEFAULT_URL, timeout=DEFAULT_TIMEOUT):
        self.portlet_title = portlet_title
        self.count = count
        self.url = url
        self.timeout = timeout


class Renderer(base.DeferredRenderer):
    render_full = ZopeTwoPageTemplateFile('dmccrss.pt')
    @property
    def initializing(self):
        u'''Return True if the feed isn't yet loaded (deferred), else False'''
        feed = self._getFeed()
        return not feed.loaded or feed.needs_update
    def deferred_update(self):
        u'''Update eventually'''
        self._getFeed().update()
    def update(self):
        u'''Update before rendering without regard to KSS'''
        self.deferred_update()
    def _getFeed(self):
        u'''Return the feed; don't update it'''
        feed = FEED_DATA.get(self.data.url, None)
        if feed is None:
            feed = FEED_DATA[self.data.url] = DMCCRSSFeed(self.data.url, self.data.timeout)
        return feed
    @property
    def url(self):
        return self._getFeed().url
    @property
    def siteurl(self):
        return self._getFeed().siteurl
    @property
    def feedlink(self):
        return self.data.url.replace("http://", "feed://")
    @property
    def title(self):
        return getattr(self.data, 'portlet_title', '') or self._getFeed().title
    @property
    def feedAvailable(self):
        return self._getFeed().ok
    @property
    def items(self):
        return self._getFeed().items[:self.data.count]
    @property
    def enabled(self):
        return self._getFeed().ok


class AddForm(base.AddForm):
    schema = IDMCCRSSPortlet
    label = _(u'Add DMCC RSS Portlet')
    description = _(u'Displays RSS from the DMCC which is … unusual.')
    def create(self, data):
        return Assignment(
            portlet_title=data.get('portlet_title', DEFAULT_TITLE),
            count=data.get('count', DEFAULT_COUNT),
            url=data.get('url', DEFAULT_URL),
            timeout=data.get('timeout', DEFAULT_TIMEOUT)
        )


class EditForm(base.EditForm):
    schema = IDMCCRSSPortlet
    label = _(u'Edit DMCC RSS Portlet')
    description = _(u"Edits portlet which displays a DMCC RSS feed which is … unusual.")
