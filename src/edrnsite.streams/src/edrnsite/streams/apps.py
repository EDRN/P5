# encoding: utf-8

'''🦦 EDRN Site streams: Django application.'''

from django.apps import AppConfig


class EDRNSiteStreams(AppConfig):
    '''Early Detection Research Network site streams.'''
    name = 'edrnsite.streams'
    label = 'edrnsitestreams'
    verbose_name = 'EDRN Site: streams'
