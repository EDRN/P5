# -*- coding: utf-8 -*-

from . import PACKAGE_NAME
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2
import eke.knowledge, pkg_resources, urllib2, urllib, httplib, eea.facetednavigation


class TestSchemeHandler(urllib2.BaseHandler):
    u'''Testing-only URL scheme ``testscheme``.'''
    def testscheme_open(self, req):
        try:
            selector = req.get_selector()
            path = 'tests/data/' + selector.split('/')[-1] + '.rdf'
            if pkg_resources.resource_exists(PACKAGE_NAME, path):
                return urllib.addinfourl(
                    pkg_resources.resource_stream(PACKAGE_NAME, path),
                    httplib.HTTPMessage(open('/dev/null')),
                    req.get_full_url(),
                    200
                )
            else:
                raise urllib2.URLError('Not found')
        except Exception as ex:
            raise urllib2.URLError('Not found (%r)' % unicode(ex))


class EkeKnowledgeLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=eea.facetednavigation)
        self.loadZCML(package=eke.knowledge)
        urllib2.install_opener(urllib2.build_opener(TestSchemeHandler))

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'eke.knowledge:default')


EKE_KNOWLEDGE_FIXTURE = EkeKnowledgeLayer()


EKE_KNOWLEDGE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(EKE_KNOWLEDGE_FIXTURE,),
    name='EkeKnowledgeLayer:IntegrationTesting',
)


EKE_KNOWLEDGE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(EKE_KNOWLEDGE_FIXTURE,),
    name='EkeKnowledgeLayer:FunctionalTesting',
)


EKE_KNOWLEDGE_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        EKE_KNOWLEDGE_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='EkeKnowledgeLayer:AcceptanceTesting',
)
