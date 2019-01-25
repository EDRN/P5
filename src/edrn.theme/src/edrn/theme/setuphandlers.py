# -*- coding: utf-8 -*-
from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer
import transaction


PREFERRED_THEME = 'barceloneta'


@implementer(INonInstallable)
class HiddenProfiles(object):

    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            'edrn.theme:uninstall',
        ]


def post_install(context):
    """Post install script"""
    # Do something at the end of the installation of this package.
    # activateBarcelonetaTheme(context)
    pass


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.
    pass
