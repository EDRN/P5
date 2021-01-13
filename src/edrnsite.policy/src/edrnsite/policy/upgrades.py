# -*- coding: utf-8 -*-

from . import PACKAGE_NAME
from .setuphandlers import publish
from .utils import installImage
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
    <h2>
        <img alt="Scientist working with computerized information standing in for data and resources."
            src="home-data-and-resources-image/@@images/image/thumb" class="image-left"
            title="Data and Resources" data-scale="thumb" />
        Data and Resources
    </h2>
    <ul>
      <li>
        <a href="data-and-resources/biomarkers">Biomarkers</a>
      </li>
      <li>
        <a href="data-and-resources/protocols">Protocols</a>
      </li>
      <li>
        <a href="data-and-resources/data">Data</a>
      </li>
      <li>
        <a href="data-and-resources/publications">Publications</a>
      </li>
      <li>
        <a href="data-and-resources/informatics">Informatics</a>
      </li>
      <li>
        <a href="data-and-resources/sample-reference-sets">Specimen Reference Sets</a>
      </li>
    </ul>
  </div>
  <div class="homeWork">
    <h2>
        <img alt="Scientists working together in a laboratory standing in for working with EDRN."
            src="home-work-with-edrn-image/@@images/image/thumb" class="image-left"
            title="Work with EDRN" data-scale="thumb" />
        Work with EDRN
    </h2>
    <ul>
      <li>
        <li><a href="work-with-edrn/associate-membership-program">Associate Membership</a> Program</li>
        <li><a href="http://www.compass.fhcrc.org/edrnnci/bin/search/search.asp?t=search&cer=&rd_deny=z0&f32=96p&etc">Find a Sponsor</a></li>
        <li><a href="work-with-edrn/validation-study-proposals">Propose a Study</a></li>
        <li><a href="work-with-edrn/public-private-partnerships">Public-Private Partnerships</a></li>
      <li>
        <a href="work-with-edrn/advocacy-groups">Advocacy Groups</a>
      </li>
    </ul>
  </div>
  <div class="homeNews">
    <h2>
        <img alt="Scientists meeting together at a conference table."
            src="home-news-and-events/@@images/image/thumb" class="image-left"
            title="News and Events" data-scale="thumb" />
        News and Events
    </h2>
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
    <h2>
        <img alt="Scientists examining things closely with a microscope."
            src="home-about-edrn-image/@@images/image/thumb" class="image-left"
            title="About EDRN" data-scale="thumb" />
        About EDRN
    </h2>
    <ul>
      <li>
        <a href="about/highlights">Accomplishments</a>
      </li>
      <li>
        <a href="about/mission-and-structure/sites">Site List</a>
      </li>
      <li>
        <a href="about/members-list">Member List</a>
      </li>
      <li>
        <a href="about/mission-and-structure/groups">Groups &amp; Committees</a>
      </li>
    </ul>
  </div>
</div>
'''

_ADMONISHMENTS_DESC = u'''Various warnings, provisos, stipulations, conditions, caveats, notifications of
domestic and international surveillance, riders, clauses, and qualifications about what logging into this
site entails and the circumstances of doing so.'''
_ADMONISHMENTS_BODY = u'''
  <h1>Important Login Information</h1>
  <p>Before logging in, please review <em>all</em> of the pertinent information that follows in this section.</p>
  <h2>Vital Links</h2>
  <p>The following links may be informative and/or provide utility for changing or recovering your password:</p>
  <ul>
    <li>The <a href="https://www.compass.fhcrc.org/enterEDRN/" data-linktype="external" data-val="https://www.compass.fhcrc.org/enterEDRN/">Data Management and Coordinating Center's "secure" website</a></li>
    <li><a href="https://www.compass.fhcrc.org/edrns/pub/user/resetPwd.aspx?t=pwd&amp;sub=form&amp;w=1&amp;p=3&amp;why=4&amp;are=5&amp;these=6&amp;extra=7&amp;parameters=8&amp;here=questionMark" data-linktype="external" data-val="https://www.compass.fhcrc.org/edrns/pub/user/resetPwd.aspx?t=pwd&amp;sub=form&amp;w=1&amp;p=3&amp;why=4&amp;are=5&amp;these=6&amp;extra=7&amp;parameters=8&amp;here=questionMark">Forgot your password</a>?</li>
    <li>Need to <a href="https://www.compass.fhcrc.org/edrns/pub/user/changePwd.aspx?t=pwd&amp;sub=form&amp;w=1&amp;p=3&amp;and=4&amp;many=5&amp;extra=6&amp;parameters=7&amp;too=exclamationPoint" data-linktype="external" data-val="https://www.compass.fhcrc.org/edrns/pub/user/changePwd.aspx?t=pwd&amp;sub=form&amp;w=1&amp;p=3&amp;and=4&amp;many=5&amp;extra=6&amp;parameters=7&amp;too=exclamationPoint">change your password</a>?</li>
    <li>
      <a href="https://www.compass.fhcrc.org/edrns/pub/user/application.aspx?t=app&amp;sub=form1&amp;w=1&amp;p=3&amp;q=4&amp;r=5&amp;s=6&amp;extra1=1&amp;extra2=2&amp;extra3=3" data-linktype="external" data-val="https://www.compass.fhcrc.org/edrns/pub/user/application.aspx?t=app&amp;sub=form1&amp;w=1&amp;p=3&amp;q=4&amp;r=5&amp;s=6&amp;extra1=1&amp;extra2=2&amp;extra3=3">Sign up with EDRN</a>
    </li>
  </ul>
  <h2>Biomarker Information</h2>
  <p>Biomarker information hosted on the public portal includes both published and unpublished research results from the Early Detection Research Network (EDRN). Summary information describing biomarkers and the associated scientific data that are being researched is provided for all biomarkers captured by the program. Access to <em>unpublished</em> biomarker research results under development by the EDRN is currently <em>only</em> available to EDRN members. In this case, members are provided a username and password that will grant them access to specific data that is hosted on the portal.</p>
  <p>If you are an EDRN member and need a user name and password please complete the <a href="https://www.compass.fhcrc.org/edrns/pub/user/application.aspx?t=app&amp;sub=form1&amp;w=1&amp;p=3&amp;q=4&amp;r=5&amp;s=6&amp;extra1=1&amp;extra2=2&amp;extra3=3" data-linktype="external" data-val="https://www.compass.fhcrc.org/edrns/pub/user/application.aspx?t=app&amp;sub=form1&amp;w=1&amp;p=3&amp;q=4&amp;r=5&amp;s=6&amp;extra1=1&amp;extra2=2&amp;extra3=3">New User Application</a> which is handled by the Data Management and Coordinating Center (DMCC).</p>
  <h2>US Government Warning</h2>
  <p>This warning banner provides privacy and security notices consistent with applicable federal laws, directives, and other federal guidance for accessing this Government system, which includes ⑴ this computer network, ⑵ all computers connected to this network, and ⑶ all devices and storage media attached to this network or to a computer on this network.</p>
  <p>This system is provided for Government-authorized use only. Unauthorized or improper use of this system is prohibited and may result in disciplinary action and/or civil and criminal penalties. Personal use of social media and networking sites on this system is limited as to not interfere with official work duties and is subject to monitoring.</p>
  <p>By using this system, you understand and consent to the following:</p>
  <ul>
    <li>The Government may monitor, record, and audit your system usage, including usage of personal devices and email systems for official duties or to conduct HHS business. Therefore, you have no reasonable expectation of privacy regarding any communication or data transiting or stored on this system. At any time, and for any lawful Government purpose, the government may monitor, intercept, and search and seize any communication or data transiting or stored on this system.</li>
    <li>Any communication or data transiting or stored on this system may be disclosed or used for any lawful Government purpose.</li>
  </ul>
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
    for ident, fn, ct, title, desc in (
        ('home-data-and-resources-image', u'nci-sci.jpg', 'image/jpeg', u'Data and Resources Image', u'A scientist using a computer to access scientific data and resources'),
        ('home-work-with-edrn-image', u'nci-vol-2423-150.jpg', 'image/jpeg', u'Work with EDRN Image', u'Several scientists working together in a laboratory setting.'),
        ('home-news-and-events', u'nci-vol-3747-150.jpg', 'image/jpeg', u'News and Events Image', u'Scientists meeting together at a conference table to possibly work on news and events.'),
        ('home-about-edrn-image', u'nci-vol-8000-150.jpg', 'image/jpeg', u'About EDRN Image', u'A pair of scientists examining things closely with a microscope.')
    ):
        installImage(portal, fn, ident, title, desc, ct)
    frontPage = createContentInContainer(
        portal,
        'Document',
        id='front-page',
        title=u'Early Detection Research Network (EDRN)',
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


def installLoginAdmonishments(setupTool, logger=None):
    if logger is None: logger = logging.getLogger(__name__)
    portal = plone.api.portal.get()
    try:
        administrivia = portal.unrestrictedTraverse('administrivia')
    except KeyError:
        administrivia = createContentInContainer(
            portal,
            'Folder',
            id='administrivia',
            title=u'Administrivia',
            description=u'Objects used to support the portal itself.'
        )
    if 'login-admonishments' in administrivia.keys():
        logger.info(u'Already have a login admonishments page, not overwriting it')
        return
    admonishments = createContentInContainer(
        administrivia,
        'Document',
        id='login-admonishments',
        title=u'Login Admonishments',
        description=_ADMONISHMENTS_DESC,
        text=RichTextValue(_ADMONISHMENTS_BODY, 'text/html', 'text/x-html-safe')
    )
    publish(admonishments)


def setLabcasRDF(setupTool, logger=None):
    '''Use new RDF for science data ingest, LabCAS 2.0-style'''
    if logger is None: logger = logging.getLogger(__name__)
    portal = plone.api.portal.get()
    try:
        scienceData = portal.unrestrictedTraverse('data-and-resources/data')
        logger.info(u'Setting RDF data sources for %r', scienceData)
        scienceData.rdfDataSources = [u'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/labcas/@@rdf']
    except KeyError:
        logger.info(u'No science data folder found in data-and-resources/data; not updating its RDF URLs')


# Boilerplate from paster template; leaving for posterity:
# from plone.app.upgrade.utils import loadMigrationProfile
# def reload_gs_profile(context):
#    loadMigrationProfile(context, 'profile-edrnsite.policy:default',)
