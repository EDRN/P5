# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from edrn.theme.testing import EDRN_THEME_INTEGRATION_TESTING  # noqa

import unittest


class TestSetup(unittest.TestCase):
    """Test that edrn.theme is properly installed."""

    layer = EDRN_THEME_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if edrn.theme is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'edrn.theme'))

    def test_browserlayer(self):
        """Test that IEdrnThemeLayer is registered."""
        from edrn.theme.interfaces import (
            IEdrnThemeLayer)
        from plone.browserlayer import utils
        self.assertIn(
            IEdrnThemeLayer,
            utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = EDRN_THEME_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer.uninstallProducts(['edrn.theme'])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if edrn.theme is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'edrn.theme'))

    def test_browserlayer_removed(self):
        """Test that IEdrnThemeLayer is removed."""
        from edrn.theme.interfaces import \
            IEdrnThemeLayer
        from plone.browserlayer import utils
        self.assertNotIn(
            IEdrnThemeLayer,
            utils.registered_layers())
