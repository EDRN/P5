# -*- coding: utf-8 -*-

u'''Layers and fixtures for the EDRN theme'''

from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import edrn.theme


class EdrnThemeLayer(PloneSandboxLayer):
    u'''Test layer for the EDRN theme: loads the ``edrn.theme`` Zope confguration
    at Zope set up and applies the ``edrn.theme`` profile at Plone set up.
    '''
    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=edrn.theme)
        z2.installProduct(app, 'edrn.theme')

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'edrn.theme:default')

    def teatDownZope(self, app):
        z2.uninstallProduct(app, 'edrn.theme')


EDRN_THEME_FIXTURE = EdrnThemeLayer()


EDRN_THEME_INTEGRATION_TESTING = IntegrationTesting(
    bases=(EDRN_THEME_FIXTURE,),
    name='EdrnThemeLayer:IntegrationTesting',
)


EDRN_THEME_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(EDRN_THEME_FIXTURE,),
    name='EdrnThemeLayer:FunctionalTesting',
)


EDRN_THEME_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        EDRN_THEME_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='EdrnThemeLayer:AcceptanceTesting',
)
