# encoding: utf-8

u'''Panel of biomarkers'''

from . import _
from .biomarker import BiomarkerView, IBiomarker
from collective import dexteritytextindexer
from plone.app.vocabularies.catalog import CatalogSource
from z3c.relationfield.schema import RelationChoice, RelationList


class IBiomarkerPanel(IBiomarker):
    u'''A panel of biomarkers that itself behaves as a single (yet composite) biomarker.'''
    dexteritytextindexer.searchable('members')
    members = RelationList(
        title=_(u'Member Markers'),
        description=_(u'Biomarkers that are a part of this panel'),
        required=False,
        value_type=RelationChoice(
            title=_(u'Member Marker'),
            description=_(u"A biomarker that's part of a panel."),
            source=CatalogSource(IBiomarker.__identifier__)
        )
    )


class View(BiomarkerView):
    def getType(self):
        return u'panel'
