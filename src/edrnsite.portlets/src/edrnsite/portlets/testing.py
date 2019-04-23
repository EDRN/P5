# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import edrnsite.portlets


class EdrnsitePortletsLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=edrnsite.portlets)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'edrnsite.portlets:default')
        # TODO: set up some test content?
        # applyProfile(portal, 'plone.app.contenttypes:default')


EDRNSITE_PORTLETS_FIXTURE = EdrnsitePortletsLayer()


EDRNSITE_PORTLETS_INTEGRATION_TESTING = IntegrationTesting(
    bases=(EDRNSITE_PORTLETS_FIXTURE,),
    name='EdrnsitePortletsLayer:IntegrationTesting',
)


EDRNSITE_PORTLETS_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(EDRNSITE_PORTLETS_FIXTURE,),
    name='EdrnsitePortletsLayer:FunctionalTesting',
)


EDRNSITE_PORTLETS_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        EDRNSITE_PORTLETS_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='EdrnsitePortletsLayer:AcceptanceTesting',
)
