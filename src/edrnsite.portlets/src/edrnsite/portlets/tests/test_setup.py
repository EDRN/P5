# -*- coding: utf-8 -*-
"""Setup tests for this package."""

from edrnsite.portlets.testing import EDRNSITE_PORTLETS_INTEGRATION_TESTING  # noqa
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from Products.CMFPlone.utils import get_installer

import unittest


class TestSetup(unittest.TestCase):
    """Test that edrnsite.portlets is properly installed."""

    layer = EDRNSITE_PORTLETS_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = get_installer(self.portal)

    def test_product_installed(self):
        """Test if edrnsite.portlets is installed."""
        self.assertTrue(self.installer.is_product_installed('edrnsite.portlets'))


class TestUninstall(unittest.TestCase):

    layer = EDRNSITE_PORTLETS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = get_installer(self.portal)
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer.uninstall_product('edrnsite.portlets')
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if edrnsite.portlets is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled('edrnsite.portlets'))
