# encoding: utf-8

u'''Knowledge control panel'''


from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from eke.knowledge import _
from eke.knowledge.interfaces import IPanel
from eke.knowledge.rdfingestor import DAWN_OF_TIME


class PanelEditForm(RegistryEditForm):
    u'''Edit form for knowledge control panel'''
    schema = IPanel
    label = _(u'Knowledge Controls')
    description = _(u'Control panel for EDRN Knowledge Environment')
    def applyChanges(self, data):
        resetIngestState = data.get('resetIngestState', False)
        if resetIngestState:
            data['ingestEnabled'], data['resetIngestState'], data['ingestStart'] = True, False, DAWN_OF_TIME
        super(PanelEditForm, self).applyChanges(data)


class KnowledgeControlPanel(ControlPanelFormWrapper):
    u'''Knowledge control panel'''
    form = PanelEditForm
