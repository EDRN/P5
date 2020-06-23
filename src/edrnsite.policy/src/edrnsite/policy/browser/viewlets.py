# encoding: utf-8

u'''Policy Viewlets'''

from plone.app.layout.viewlets.common import ViewletBase
from plone.registry.interfaces import IRegistry
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import getUtility
import pkg_resources


class EDRNDevWarningViewlet(ViewletBase):
    u'''Viewlet to show that the portal you're viewing is in development ⚠️'''
    index = ViewPageTemplateFile('dev-warning.pt')


class EDRNColophonViewlet(ViewletBase):
    u'''Viewlet for the EDRN-specific colophon that we hope doesn't reveal too much'''
    index = ViewPageTemplateFile('edrn-colophon.pt')
    def update(self):
        super(EDRNColophonViewlet, self).update()
        registry = getUtility(IRegistry)
        self.version = registry.get(u'edrnsite.policy.portal.version', u'«unknown»')
