# encoding: utf-8

from .knowledgeobject import IKnowledgeObject
from five import grok


class IResource(IKnowledgeObject):
    u'''A miscellaneous resource.'''


IResource.setTaggedValue('predicates', {
    u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Description': ('title', False)
})
IResource.setTaggedValue('fti', 'eke.knowledge.resource')
IResource.setTaggedValue('typeURI', u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#ExternalResource')


class View(grok.View):
    grok.context(IResource)
    grok.require('zope2.View')
