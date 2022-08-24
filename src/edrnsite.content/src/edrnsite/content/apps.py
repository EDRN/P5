# encoding: utf-8

'''😌 EDRN Site Content: Django application.'''

from django.apps import AppConfig


class EDRNSiteContent(AppConfig):
    '''The Early Detection Research Network content types.'''
    name = 'edrnsite.content'
    label = 'edrnsitecontent'
    verbose_name = 'EDRN Site: content'
