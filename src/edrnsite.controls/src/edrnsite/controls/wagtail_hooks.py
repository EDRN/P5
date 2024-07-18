# encoding: utf-8

'''🎛 EDRN Site Controls: Wagtail hooks and interceptors.'''

from .models import Informatics
from django.http import HttpRequest
from django.template.loader import render_to_string
from wagtail import hooks
from wagtail.admin.ui.components import Component


class EDRNSiteControlsControlPanel(Component):
    '''Custom control panel for EDRN site controls.'''

    name = 'edrnsite_controls'
    order = 210

    def __init__(self, request: HttpRequest):
        self.request = request

    def render_html(self, parent_context: list) -> str:
        context = {'my_ip': Informatics.for_request(self.request).ip_address}
        return render_to_string('edrnsite.controls/edrnsite-controls.html', context, request=self.request)


@hooks.register('construct_homepage_panels')
def add_ingest_controls(request: HttpRequest, panels: list):
    '''Add the custom EDRN site controls control panel.'''
    panels.append(EDRNSiteControlsControlPanel(request))
