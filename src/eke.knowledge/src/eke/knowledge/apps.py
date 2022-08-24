# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: Django application.'''

from django.apps import AppConfig


class EDRNKnowledgeEnvironment(AppConfig):
    name = 'eke.knowledge'
    label = 'ekeknowledge'
    verbose_name = 'EDRN Knowledge Enviroment: base knowledge'

    def ready(self):
        from . import signals  # noqa
