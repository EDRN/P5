# encoding: utf-8

'''Drop down menus'''


from Products.CMFCore.interfaces import IFolderish
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer as ccic
from plone.namedfile.file import NamedBlobImage
from Products.CMFCore.interfaces import IWorkflowTool
from Products.CMFCore.WorkflowCore import WorkflowException
from zope.component import getUtility
import logging, pkg_resources

_logger = logging.getLogger(__name__)


def publish(context, workflowTool=None):
    try:
        if workflowTool is None:
            workflowTool = getUtility(IWorkflowTool)
        workflowTool.doActionFor(context, action='publish')
        context.reindexObject()
    except WorkflowException:
        pass
    if IFolderish.providedBy(context):
        for itemID, subItem in context.contentItems():
            publish(subItem, workflowTool)


def getPageText(name):
    return pkg_resources.resource_stream(__name__, u'content/pages/' + name + u'.html').read().decode('utf-8')


def installImage(context, fn, ident, title, desc, contentType):
    imageData = pkg_resources.resource_stream(__name__, u'content/pages/' + fn).read()
    return ccic(
        context,
        'Image',
        id=ident,
        title=title,
        description=desc,
        image=NamedBlobImage(data=imageData, contentType=contentType, filename=fn)
    )


def createFolderWithOptionalDefaultPageView(context, ident, title, desc, body=None):
    '''Create a Folder with object identifier ``ident`` and title ``title`` as well as description
    ``desc`` in the ``context`` object. If ``body`` is not None, then also create a Page in the
    Folder with the same title and description and the given ``body`` text, and make the Page the
    default view of the folder.
    '''
    if ident in context.keys(): context.manage_delObjects([ident])
    folder = ccic(context, 'Folder', id=ident, title=title, description=desc)
    if body:
        body = RichTextValue(body,  'text/html', 'text/x-html-safe')
        page = ccic(folder, 'Document', id=ident, title=title, description=desc, text=body)
        folder.setDefaultPage(page.id)
    else:
        folder.setLayout('summary_view')
    publish(folder)
    return folder
