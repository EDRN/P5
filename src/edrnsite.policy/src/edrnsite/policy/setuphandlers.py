# -*- coding: utf-8 -*-


from plone.dexterity.utils import createContentInContainer
from plone.portlet.collection.collection import Assignment as CollectionPortletAssignment
from plone.portlets.interfaces import ILocalPortletAssignable, IPortletManager, IPortletAssignmentMapping
from Products.CMFCore.interfaces import IFolderish
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFPlone.interfaces import INonInstallable
from zope.component import getUtility, getMultiAdapter
from zope.container import contained
from zope.container.interfaces import INameChooser
from zope.interface import implementer
import plone.api, logging


_logger = logging.getLogger(__name__)


_ITEMS_TO_DELETE = ('news', 'events', 'Members')


@implementer(INonInstallable)
class HiddenProfiles(object):

    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            'edrnsite.policy:uninstall',
        ]


def _publish(context, workflowTool=None):
    try:
        if workflowTool is None:
            workflowTool = plone.api.portal.get_tool('portal_workflow')
        workflowTool.doActionFor(context, action='publish')
        context.reindexObject()
    except WorkflowException:
        pass
    if IFolderish.providedBy(context):
        for itemID, subItem in context.contentItems():
            _publish(subItem, workflowTool)


def _removePortlets(portal):
    u'''Remove all portlets everywhere. See
    https://community.plone.org/t/remove-the-default-portlet-assignments-using-genericsetup/2857/5
    for more.'''
    catalog = plone.api.portal.get_tool('portal_catalog')
    all_content = catalog(
        show_inactive=True,
        language='ALL',
        object_provides=ILocalPortletAssignable.__identifier__
    )
    all_content = [content.getObject() for content in all_content]
    all_content = list(all_content) + [portal]
    for content in all_content:
        for manager_name in ['plone.leftcolumn', 'plone.rightcolumn']:
            manager = getUtility(IPortletManager, name=manager_name, context=content)
            mapping = getMultiAdapter((content, manager), IPortletAssignmentMapping)
            for pid, assignment in mapping.items():
                fixing_up = contained.fixing_up
                contained.fixing_up = True
                del mapping[pid]
                contained.fixing_up = fixing_up


def _getAdminFolder(portal):
    if 'adminisitrivia' in portal.keys():
        return portal.unrestrictedTraverse('adminisitrivia')
    else:
        folder = createContentInContainer(
            portal,
            'Folder',
            title=u'Administrivia',
            description=u'Objects used to support the portal itself.',
            exclude_from_nav=True
        )
        _publish(folder)
        return folder


def _addQuickLinks(portal):
    u'''Add the Quick Links portlet.'''
    folder = _getAdminFolder(portal)
    if 'quick-links' in folder.keys():
        quickLinks = folder.unrestrictedTraverse('quick-links')
    else:
        quickLinks = createContentInContainer(
            folder,
            'Collection',
            title=u'Quick Links',
            description=u'A collection that lists everything tagged "quicklinks".',
            query=[{
                u'i': u'Subject',
                u'o': u'plone.app.querystring.operation.selection.any',
                u'v': [u'quicklinks']
            }],
            sort_on='sortable_title',
            sort_reversed=False,
            limit=None
        )
        for url, title, desc in (
            (u'https://prevention.cancer.gov/', u'Division of Cancer Prevention', u'The Division of Cancer Prevention is the parent organization of the Early Detection Research Network.'),
            (u'https://prevention.cancer.gov/research-groups/cancer-biomarkers', u'Cancer Biomarkers Research Group', u'The CBRG operates the Early Detection Research Network.')
        ):
            createContentInContainer(
                folder,
                'Link',
                title=title,
                description=desc,
                remoteUrl=url
            )
    _publish(folder)
    assignment = CollectionPortletAssignment(
        header=u'Quick Links',
        uid=quickLinks.UID(),
        limit=None,
        random=False,
        show_more=False,
        show_dates=False,
        exclude_context=False,
        no_icons=True,
        no_thumbs=True,
        thumb_scale=None
    )
    manager = getUtility(IPortletManager, u'plone.leftcolumn')
    mapping = getMultiAdapter((portal, manager), IPortletAssignmentMapping)
    chooser = INameChooser(mapping)
    mapping[chooser.chooseName(None, assignment)] = assignment


def post_install(context):
    """Post install script"""
    # Do something at the end of the installation of this package.
    # activateBarcelonetaTheme(context)
    portal = plone.api.portal.get()
    toDelete = []
    for item in _ITEMS_TO_DELETE:
        if item in portal.keys():
            toDelete.append(item)
    if toDelete:
        _logger.info('Deleting the following from the portal: %r', toDelete)
        portal.manage_delObjects(toDelete)
    _removePortlets(portal)
    _addQuickLinks(portal)

# Cases
# -----
#
# Add Plone site by hand, no add-ons:
#   Import about-edrn.zexp by hand status: ✅
# Add Plone site by hand, with edrnsite.policy, but auto zexp import disabled:
#   Import about-edrn.zexp by hand status: ✅
# Add Plone site with collective.recipe.plonesite (no add-ons):
#   Import about-edrn.zexp by hand status: ❌
# Add Plone site with collective.recipe.plonesite and edrnsite.polciy enabled (but auto zexp import disabled):
#   Import about-edrn.zexp by hand status: ❌
# Add Plone site with collective.recipe.plonesite and edrnsite.polciy enable, auto zexp import:
#   Status: ❌
#
# Upshot: need to come up with my own Plone5-compatible way of creating a Plone Site object with
# edrnsite.policy loaded that can also successfully import ZEXP files. Do NOT try to do this from
# within post_install! That way lies madness! *MADNESS!*


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.
    pass
