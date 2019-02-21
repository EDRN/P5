# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import edrnsite.policy, edrn.theme, pas.plugins.ldap, yafowil.plone


class EdrnsitePolicyLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=yafowil.plone)
        self.loadZCML(package=pas.plugins.ldap)
        self.loadZCML(package=edrnsite.policy)
        self.loadZCML(package=edrn.theme)
        self.loadZCML(package=eke.knowledge)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'edrnsite.policy:default')


EDRNSITE_POLICY_FIXTURE = EdrnsitePolicyLayer()


EDRNSITE_POLICY_INTEGRATION_TESTING = IntegrationTesting(
    bases=(EDRNSITE_POLICY_FIXTURE,),
    name='EdrnsitePolicyLayer:IntegrationTesting',
)


EDRNSITE_POLICY_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(EDRNSITE_POLICY_FIXTURE,),
    name='EdrnsitePolicyLayer:FunctionalTesting',
)


EDRNSITE_POLICY_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        EDRNSITE_POLICY_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='EdrnsitePolicyLayer:AcceptanceTesting',
)
