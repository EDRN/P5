# encoding: utf-8

'''📐 EDRN Metrics: Django Application'''

from django.apps import AppConfig


class EDRNMetricsConfig(AppConfig):
    '''Early Detection Research Network metrics.'''
    name = 'edrn.metrics'
    label = 'edrnmetrics'
    verbose_name = 'EDRN Metrics'
