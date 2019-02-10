# -*- coding: utf-8 -*-
from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer
import transaction, plone.api, os, logging, os.path

_logger = logging.getLogger(__name__)


@implementer(INonInstallable)
class HiddenProfiles(object):

    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            'edrnsite.policy:uninstall',
        ]


def post_install(context):
    """Post install script"""
    # Do something at the end of the installation of this package.
    # activateBarcelonetaTheme(context)


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
