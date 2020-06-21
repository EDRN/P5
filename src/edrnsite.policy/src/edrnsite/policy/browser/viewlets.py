# encoding: utf-8

u'''Policy Viewlets'''

from plone.app.layout.viewlets.common import ViewletBase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class EDRNDevWarningViewlet(ViewletBase):
    u'''Viewlet to show that the portal you're viewing is in development ⚠️'''
    index = ViewPageTemplateFile('dev-warning.pt')
