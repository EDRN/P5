# -*- coding: utf-8 -*-

from . import PACKAGE_NAME
from .setuphandlers import publish
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer
from plone.namedfile.file import NamedBlobImage
import logging, plone.api, os

PROFILE = 'profile-' + PACKAGE_NAME + ':default'

_HOME_PAGE_DESC = u'''The Early Detection Research Network (EDRN), an initiative of the National Cancer Institute (NCI), brings together dozens of institutions to help accelerate the translation of biomarker information into clinical applications and to evaluate new ways of testing cancer in its earliest stages and for cancer risk.'''
_HOME_PAGE_BODY = u'''<p><img alt="Home Page Banner Splash"
src="resolveuid/{banner}" class="image-inline" title="Home Page Banner Splash"
data-linktype="image" data-scale="" data-val="{banner}" /></p>
<div class="homeGrid">
<div class="homeData">
<h2>Data and Resources</h2>
<ul>
<li><a href="#">Biomarkers</a></li>
<li><a href="#">Protocols</a></li>
<li><a href="#">Data</a></li>
<li><a href="#">Tools and Specimens</a></li>
<li><a href="#">Informatics Tools</a></li>
<li><a href="#">Publications</a></li>
</ul>
</div>
<div class="homeWork">
<h2>Work with EDRN</h2>
<ul>
<li><a href="#">Associate Membership</a></li>
<li><a href="#">Funding Opportunities</a></li>
<li><a href="#">Propose a Validation Study</a></li>
<li><a href="#">Public-Private Partnerships</a></li>
<li><a href="#">Propose a Study</a></li>
<li><a href="#">Advocacy Groups</a></li>
<li><a href="#">Request Biomarkers</a></li>
</ul>
</div>
<div class="homeNews">
<h2>News and Events</h2>
<ul>
<li><a href="#">EDRN Newsletter</a></li>
<li><a href="#">Prevention Science blogs</a></li>
<li><a href="#">Meeting Registration</a></li>
<li><a href="#">Meeting Reports</a></li>
</ul>
</div>
</div>'''


def reloadViewlets(setupTool, logger=None):
    setupTool.runImportStepFromProfile(PROFILE, 'viewlets')


def reloadRegistry(setupTool, logger=None):
    setupTool.runImportStepFromProfile(PROFILE, 'plone.app.registry')


def reloadPortlets(setupTool, logger=None):
    setupTool.runImportStepFromProfile(PROFILE, 'portlets')


def install2020SOWHomePage(setupTool, logger=None):
    if logger is None: logger = logging.getLogger(__name__)
    portal = plone.api.portal.get()
    try: portal.manage_delObjects(['front-page'])
    except AttributeError: pass
    # Shouldn't we use pkg_resources here?
    with open(os.path.join(os.path.dirname(__file__), 'content', 'tentative-banner.png'), 'rb') as f:
        imageData = f.read()
    banner = createContentInContainer(
        portal,
        'Image',
        id='tentative-banner',
        title=u'EDRN Banner',
        description=u'A tentative banner image of abstract biomarker research.',
        image=NamedBlobImage(data=imageData, contentType='image/png', filename=u'tentative-banner.png')
    )
    frontPage = createContentInContainer(
        portal,
        'Document',
        id='front-page',
        title=u'EDRN',
        description=_HOME_PAGE_DESC,
        text=RichTextValue(_HOME_PAGE_BODY.format(banner=banner.UID()), 'text/html', 'text/x-html-safe')
    )
    portal.setDefaultPage(frontPage.id)
    publish(frontPage)


# Boilerplate from paster template; leaving for posterity:
# from plone.app.upgrade.utils import loadMigrationProfile
# def reload_gs_profile(context):
#    loadMigrationProfile(context, 'profile-edrnsite.policy:default',)
