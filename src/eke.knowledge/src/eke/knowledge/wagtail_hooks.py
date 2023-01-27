# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: Wagtail hooks and interceptors.'''

from .models import RDFIngest, KnowledgeFolder
from django.core.cache import cache
from django.http import HttpRequest
from django.template.loader import render_to_string
from wagtail.admin.ui.components import Component
from wagtail.core import hooks
import socket


class IngestControlPanel(Component):
    '''Custom control panel for RDF ingest.'''

    name = 'ingest_controls'
    order = 200

    def __init__(self, request: HttpRequest):
        self.request = request

    def render_html(self, parent_context: list) -> str:
        lock = cache.lock('full_ingest')
        settings = RDFIngest.for_request(self.request)
        folders = KnowledgeFolder.objects.all().order_by('ingest_order')
        context = {
            'last_ingest_start': settings.last_ingest_start,
            'last_ingest_duration': settings.last_ingest_duration,
            'ingest_running': lock.locked(),
            'knowledge_folders': folders,
            'hostname': socket.getfqdn()
        }
        return render_to_string('eke.knowledge/ingest-controls.html', context, request=self.request)


@hooks.register('construct_homepage_panels')
def add_ingest_controls(request: HttpRequest, panels: list):
    '''Add the custom ingest control panel.'''
    panels.append(IngestControlPanel(request))
