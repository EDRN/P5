# encoding: utf-8


from .dublincore import TITLE_URI, DESCRIPTION_URI
from .knowledgeobject import IKnowledgeObject


class IBodySystem(IKnowledgeObject):
    u'''Body system, aka "organ".'''


IBodySystem.setTaggedValue('predicates', {
    TITLE_URI: ('title', False),
    DESCRIPTION_URI: ('description', False)
})
IBodySystem.setTaggedValue('fti', 'eke.knowledge.bodysystem')
IBodySystem.setTaggedValue('typeURI', u'http://edrn.nci.nih.gov/rdf/types.rdf#BodySystem')
