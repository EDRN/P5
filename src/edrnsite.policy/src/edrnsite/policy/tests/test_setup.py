# -*- coding: utf-8 -*-
"""Setup tests for this package."""

from edrnsite.policy.testing import EDRNSITE_POLICY_INTEGRATION_TESTING  # noqa
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.registry.interfaces import IRegistry
from plone.app.viewletmanager.interfaces import IViewletSettingsStorage
from zope.component import getUtility

import unittest


class TestSetup(unittest.TestCase):
    """Test that edrnsite.policy is properly installed."""

    layer = EDRNSITE_POLICY_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if edrnsite.policy is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'edrnsite.policy'))

    def test_browserlayer(self):
        """Test that IEdrnsitePolicyLayer is registered."""
        from edrnsite.policy.interfaces import (
            IEdrnsitePolicyLayer)
        from plone.browserlayer import utils
        self.assertIn(
            IEdrnsitePolicyLayer,
            utils.registered_layers())

    def test_viewlets(self):
        '''Make sure the custom viewlet is there'''
        storage = getUtility(IViewletSettingsStorage)
        viewlets = list(storage.getOrder(u'plone.portaltop', 'Plone Default'))
        self.assertEqual(u'edrn.dev_warning', viewlets[0])


class TestUninstall(unittest.TestCase):

    layer = EDRNSITE_POLICY_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer.uninstallProducts(['edrnsite.policy'])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if edrnsite.policy is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'edrnsite.policy'))

    def test_browserlayer_removed(self):
        """Test that IEdrnsitePolicyLayer is removed."""
        from edrnsite.policy.interfaces import \
            IEdrnsitePolicyLayer
        from plone.browserlayer import utils
        self.assertNotIn(
            IEdrnsitePolicyLayer,
            utils.registered_layers())
