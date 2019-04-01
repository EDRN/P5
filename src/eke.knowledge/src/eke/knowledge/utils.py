# encoding: utf-8

u'''EKE Utilities'''


from Products.CMFCore.interfaces import IFolderish
from Products.CMFCore.WorkflowCore import WorkflowException
from zope.intid.interfaces import IIntIds
from z3c.relationfield import RelationValue
from zope import schema
from zope.component import getUtility
from zope.interface import Invalid
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

def publish(context, workflowTool=None):
    u'''Publish ``context`` item and all of its children with the ``workflowTool``, unless the ``workflowTool``
    is None, in which case we'll look it up ourselves.'''
    try:
        if workflowTool is None: workflowTool = plone.api.portal.get_tool('portal_workflow')
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
        _logger.info(u'Field %s does not exist in %s', fieldName, fti)
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
