# encoding: utf-8

u'''Provide convenient lookups for RDF subject URIs'''

from Products.Five import BrowserView
import plone.api, httplib


class DataDispatcher(BrowserView):
    u'''Data dispatcher'''
    def __call__(self):
        subjectURI = self.request.form.get('subjectURI')
        if not subjectURI:
            raise ValueError('The subjectURI parameter is required')
        catalog = plone.api.portal.get_tool('portal_catalog')
        results = catalog(identifier=subjectURI)
        if len(results) == 0:
            self.request.response.setStatus(httplib.NOT_FOUND, 'Not found')
        elif len(results) > 1:
            raise ValueError('The subjectURI {} matched more than one ({}) objects'.format(subjectURI, len(results)))
        else:
            self.request.response.redirect(results[0].getURL())
