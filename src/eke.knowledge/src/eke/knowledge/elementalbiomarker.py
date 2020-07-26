# encoding: utf-8


u'''Elemental biomarker.'''

from . import _
from .biomarker import BiomarkerView, IBiomarker
from zope import schema


class IElementalBiomarker(IBiomarker):
    u'''A single, actual biomarker.'''
    biomarkerType = schema.TextLine(
        title=_(u'Biomarker Type'),
        description=_(u'The general category, kind, or class of this biomarker.'),
        required=False
    )


class View(BiomarkerView):
    def getType(self):
        return u'elemental'
