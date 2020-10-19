# -*- coding: utf-8 -*-

from . import PACKAGE_NAME
from .setuphandlers import publish
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer
from plone.namedfile.file import NamedBlobImage
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
import logging, plone.api, os

PROFILE = 'profile-' + PACKAGE_NAME + ':default'

_HOME_PAGE_DESC = u''  # Kara hates the text display, but Plone doesn't provide a way to keep metadata but not show it
_HOME_PAGE_BODY = u'''<p style='text-align: center;'><img alt="Home Page Banner Splash"
src="resolveuid/{banner}" class="image-inline" title="Home Page Banner Splash"
data-linktype="image" data-scale="" data-val="{banner}" /></p>
<?xml version="1.0"?>
<div class="homeGrid">
  <div class="homeData">
    <h2>Data and Resources</h2>
    <ul>
      <li>
        <a href="biomarkers">Biomarkers</a>
      </li>
      <li>
        <a href="protocols">Protocols</a>
      </li>
      <li>
        <a href="data">Data</a>
      </li>
      <li>
        <a href="publications">Publications</a>
      </li>
      <li>
        <a href="informatics">Informatics Tools</a>
      </li>
      <li>
        <a href="resources/sample-reference-sets">Specimen Reference Sets</a>
      </li>
    </ul>
  </div>
  <div class="homeWork">
    <h2>Work with EDRN</h2>
    <ul>
      <li>
        Collaborative Opportunities
        <ul><li><a href="work-with-edrn/colops/assoc">Associate Membership</a> Program</li><li><a href="colops">Find/Participate in a Collaborative Study</a></li><li><a href="colops/vsp">Propose a Study</a></li><li><a href="colops/edrn-ppp-guidelines">Public-Private Partnerships</a></li><li><a href="colops/request-for-biomarkers-1.pdf/view">Request Biomarkers</a></li></ul>
    </li>
      <li>
        <a href="/work-with-edrn/advocacy-groups">Advocacy Groups</a>
      </li>
    </ul>
  </div>
  <div class="homeNews">
    <h2>News and Events</h2>
    <ul>
      <li>
        <a href="docs/edrn-enewsletter-april-2019">EDRN Newsletter</a>
      </li>
      <li>
        <a href="https://prevention.cancer.gov/news-and-events/blog">Prevention Science blogs</a>
      </li>
      <li>
        <a href="https://www.compass.fhcrc.org/meeting/reg_edrn/edrnsc.aspx">36th Meeting Registration</a>
      </li>
      <li>
        <a href="about/groups/steering-committee/35">35th Meeting Reports</a>
      </li>
    </ul>
  </div>
  <div class="homeAbout">
    <h2>About EDRN</h2>
    <ul>
      <li>
        <a href="about/highlights">Accomplishments</a>
      </li>
      <li>
        <a href="about/sites">Site List</a>
      </li>
      <li>
        <a href="about/members-list">Member List</a>
      </li>
      <li>
        <a href="about/groups">Groups &amp; Committees</a>
      </li>
    </ul>
  </div>
</div>
'''


def reloadViewlets(setupTool, logger=None):
    setupTool.runImportStepFromProfile(PROFILE, 'viewlets')


def reloadActions(setupTool, logger=None):
    setupTool.runImportStepFromProfile(PROFILE, 'actions')


def reloadRegistry(setupTool, logger=None):
    setupTool.runImportStepFromProfile(PROFILE, 'plone.app.registry')


def reloadPortlets(setupTool, logger=None):
    setupTool.runImportStepFromProfile(PROFILE, 'portlets')


def install2020SOWHomePage(setupTool, logger=None):
    if logger is None: logger = logging.getLogger(__name__)
    portal = plone.api.portal.get()
    if 'front-page' in portal.keys():
        plone.api.content.delete(obj=portal['front-page'])
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


def install202SOWMenus(setupTool, logger=None):
    portal = plone.api.portal.get()
    from .dropDownMenus import install as installDropDownMenus
    installDropDownMenus(portal)


def dropCachedResourceRegistries(setupTool, logger=None):
    if logger is None: logger = logging.getLogger(__name__)
    registry = getUtility(IRegistry)
    for key in (
        'plone.app.caching.weakCaching.plone.content.folderView.etags',
        'plone.app.caching.weakCaching.plone.content.itemView.etags',
    ):
        try:
            current = list(registry[key])
            logger.info('Removing resourceRegistries from %s', key)
            current.remove('resourceRegistries')
            registry[key] = tuple(current)
        except (ValueError, KeyError):
            logger.info('resourceRegistries not found in %s, skipping', key)
            pass


# Boilerplate from paster template; leaving for posterity:
# from plone.app.upgrade.utils import loadMigrationProfile
# def reload_gs_profile(context):
#    loadMigrationProfile(context, 'profile-edrnsite.policy:default',)
