# -*- coding: utf-8 -*-


# This was a nice idea (auto-generate QuickLinks) but Dan wants the static HTML version instead:
# from plone.portlet.collection.collection import Assignment as CollectionPortletAssignment

from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer
import logging


_logger = logging.getLogger(__name__)


@implementer(INonInstallable)
class HiddenProfiles(object):

    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            'edrnsite.portlets:uninstall',
        ]


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.
    pass


def post_install(context):
    pass
