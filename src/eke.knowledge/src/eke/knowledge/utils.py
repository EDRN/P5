# encoding: utf-8

u'''EKE Utilities'''


from Products.CMFCore.interfaces import IFolderish
from Products.CMFCore.WorkflowCore import WorkflowException
import plone.api


# Classes
# -------

class IngestConsequences(object):
    def __init__(self, created, updated, deleted):
        self.created, self.updated, self.deleted = created, updated, deleted


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