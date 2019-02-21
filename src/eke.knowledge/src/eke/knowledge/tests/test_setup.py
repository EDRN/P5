# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from eke.knowledge.testing import EKE_KNOWLEDGE_INTEGRATION_TESTING  # noqa

import unittest


class TestSetup(unittest.TestCase):
    """Test that eke.knowledge is properly installed."""

    layer = EKE_KNOWLEDGE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if eke.knowledge is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'eke.knowledge'))

    def test_browserlayer(self):
        """Test that IEkeKnowledgeLayer is registered."""
        from eke.knowledge.interfaces import (
            IEkeKnowledgeLayer)
        from plone.browserlayer import utils
        self.assertIn(
            IEkeKnowledgeLayer,
            utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = EKE_KNOWLEDGE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer.uninstallProducts(['eke.knowledge'])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if eke.knowledge is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'eke.knowledge'))

    def test_browserlayer_removed(self):
        """Test that IEkeKnowledgeLayer is removed."""
        from eke.knowledge.interfaces import \
            IEkeKnowledgeLayer
        from plone.browserlayer import utils
        self.assertNotIn(
            IEkeKnowledgeLayer,
            utils.registered_layers())
