# encoding: utf-8

from . import _
from .bodysystem import IBodySystem
from .dublincore import TITLE_URI, DESCRIPTION_URI
from .knowledgeobject import IKnowledgeObject
from five import grok
from zope import schema


class IDisease(IKnowledgeObject):
    u'''An ailment affecting an organ or organs.'''
    affectedOrgans = schema.List(
        title=_(u'Affected Body Systems'),
        description=_(u'Body systems for which this disease is an ailment.'),
        required=False,
        value_type=schema.Object(title=_(u'Body System'), schema=IBodySystem),
        unique=True
    )
    icd9Code = schema.TextLine(
        title=_(u'ICD9 Code'),
        description=_(u'International Statistical Classifiction of Disease Code (version 9)'),
        required=False,
    )
    icd10Code = schema.TextLine(
        title=_(u'ICD10 Code'),
        description=_(u'International Statistical Classifiction of Disease Code (version 10)'),
        required=False,
    )


IDisease.setTaggedValue('predicates', {
    TITLE_URI: ('title', False),
    DESCRIPTION_URI: ('description', False),
    u'http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#icd9': ('icd9Code', False),
    u'http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#icd10': ('icd10Code', False),
    u'http://edrn.nci.nih.gov/xml/rdf/edrn.rdf#bodySystemsAffected': ('affectedOrgans', True)
})
IDisease.setTaggedValue('fti', 'eke.knowledge.disease')
IDisease.setTaggedValue('typeURI', u'http://edrn.nci.nih.gov/rdf/types.rdf#Disease')


class View(grok.View):
    grok.context(IDisease)
