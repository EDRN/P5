# encoding: utf-8

u'''EKE Utilities'''


from plone.i18n.normalizer.interfaces import IIDNormalizer
from Products.CMFCore.interfaces import IFolderish
from Products.CMFCore.interfaces import IWorkflowTool
from Products.CMFCore.WorkflowCore import WorkflowException
from z3c.relationfield import RelationValue
from zope import schema
from zope.component import getUtility
from zope.event import notify
from zope.interface import Invalid
from zope.intid.interfaces import IIntIds
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema.vocabulary import SimpleVocabulary
import plone.api, logging

_logger = logging.getLogger(__name__)


# Classes
# -------

class IngestConsequences(object):
    def __init__(self, created, updated, deleted, statements=None):
        self.created, self.updated, self.deleted, self.statements = created, updated, deleted, statements
    def __repr__(self):
        return '{}(created={},updated={},deleted={},statements={})'.format(
            self.__class__.__name__,
            len(self.created),
            len(self.updated),
            len(self.deleted),
            len(self.statements)
        )


# Functions
# ---------

def generateVocabularyFromIndex(indexName, context=None):
    u'''Generate a simple vocabulary for the unique values of the given index named ``indexName``.'''
    normalizer = getUtility(IIDNormalizer)
    catalog = plone.api.portal.get_tool('portal_catalog')
    results = list(catalog.uniqueValuesFor(indexName))
    results.sort()
    items, terms = {}, []
    for i in results:
        if i:
            token, title = normalizer.normalize(i), i
            items[token] = title
    tokens = items.keys()
    tokens.sort()
    for token in tokens:
        title = items[token]
        terms.append(SimpleVocabulary.createTerm(title, token, title))
    return SimpleVocabulary(terms)


def publish(context, workflowTool=None):
    u'''Publish ``context`` item and all of its children with the ``workflowTool``, unless the ``workflowTool``
    is None, in which case we'll look it up ourselves.'''
    try:
        if workflowTool is None: workflowTool = getUtility(IWorkflowTool)
        workflowTool.doActionFor(context, action='publish')
        context.reindexObject()
    except WorkflowException:
        pass
    if IFolderish.providedBy(context):
        for itemID, subItem in context.contentItems():
            publish(subItem, workflowTool)


def setValue(obj, fti, iface, predicate, predicateMap, values):
    u'''Look up the field of ``obj`` matching ``predicate`` in the ``predicateMap``` and set it to ``values```.
    Use the ``fti`` to warn of any issue and access fields via the ``iface``.'''
    catalog = plone.api.portal.get_tool('portal_catalog')
    fieldName, isReference = predicateMap[unicode(predicate)]
    if not values:
        _logger.info(u'Type %s needs pred %s but not given; leaving %s un-set', fti, predicate, fieldName)
        return
    field = iface.get(fieldName)
    if field is None:
        _logger.debug(u'Field %s does not exist in %s; ignoring', fieldName, fti)
        return
    fieldBinding = field.bind(obj)
    if isReference:
        idUtil = getUtility(IIntIds)
        items = [i.getObject() for i in catalog(identifier=values)]
        if len(items) != len(values):
            _logger.info(
                u'Type %s has reference predicate %s: linked to %d URIs, yet only %d found',
                fti, predicate, len(values), len(items)
            )
        intids = [idUtil.getId(i) for i in items]
        rvs = [RelationValue(i) for i in intids]
        if schema.interfaces.ICollection.providedBy(field):
            fieldBinding.set(obj, rvs)
        elif len(items) > 0:
            fieldBinding.set(obj, rvs[0])
        notify(ObjectModifiedEvent(obj))
    else:  # Non-reference field
        try:
            values = [textString.strip() for textString in values]
            if schema.interfaces.ICollection.providedBy(field):  # Multi-valued
                fieldBinding.validate(values)
                fieldBinding.set(obj, values)
            else:  # Scalar
                fieldBinding.validate(values[0])
                fieldBinding.set(obj, values[0])
        except Invalid:
            _logger.exception('Invalid data type for field %s type %s', fieldName, fti)
