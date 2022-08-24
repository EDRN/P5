# encoding: utf-8

'''🧬 EDRN Site: Django Application'''

from django.apps import AppConfig


class EDRNSitePolicyConfig(AppConfig):
    '''The Early Detection Research Network policy app.'''
    name = 'edrnsite.policy'
    label = 'edrnsitepolicy'
    verbose_name = 'EDRN Site Policy'
