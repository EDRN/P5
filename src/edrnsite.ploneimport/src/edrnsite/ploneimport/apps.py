# encoding: utf-8

'''📦 EDRN Site Import from Plone: Django application.'''

from django.apps import AppConfig


class EDRNSitePloneImport(AppConfig):
    '''Early Detection Research Network site import from Plone.'''
    name = 'edrnsite.ploneimport'
    label = 'edrnsiteploneimport'
    verbose_name = 'EDRN Site Plone Import'
