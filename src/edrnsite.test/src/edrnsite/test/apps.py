# encoding: utf-8

'''🩺 EDRN site testing: Django app.'''


from django.apps import AppConfig


class EDRNSiteTestConfig(AppConfig):
    '''Early Detection Research Network site testing.'''
    name = 'edrnsite.test'
    label = 'edrnsitetest'
    verbose_name = 'EDRN Site Test'
