# encoding: utf-8

from knowledgeobject import IKnowledgeObject


class IBodySystem(IKnowledgeObject):
    u'''Body system, aka "organ".'''


IBodySystem.setTaggedValue('predicates', {
    u'http://purl.org/dc/terms/title': ('title', False),
    u'http://purl.org/dc/terms/description': ('description', False)
})
IBodySystem.setTaggedValue('fti', 'eke.knowledge.bodysystem')
IBodySystem.setTaggedValue('typeURI', u'http://edrn.nci.nih.gov/rdf/types.rdf#BodySystem')
