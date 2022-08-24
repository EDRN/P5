# encoding: utf-8

'''🔐 EDRN Auth: Django Application'''

from django.apps import AppConfig


class EDRNAuthConfig(AppConfig):
    '''Early Detection Research Network authentication/authorization.'''
    name = 'edrn.auth'
    label = 'edrnauth'
    verbose_name = 'EDRN Auth'
