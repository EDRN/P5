# encoding: utf-8

u'''Knowledge control panel'''


from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from eke.knowledge import _
from eke.knowledge.interfaces import IPanel


class PanelEditForm(RegistryEditForm):
    u'''Edit form for knowledge control panel'''
    schema = IPanel
    label = _(u'Knowledge Controls')
    description = _(u'Control panel for EDRN Knowledge Environment')


class KnowledgeControlPanel(ControlPanelFormWrapper):
    u'''Knowledge control panel'''
    form = PanelEditForm
