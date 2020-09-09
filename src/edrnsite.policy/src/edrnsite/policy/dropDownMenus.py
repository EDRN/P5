# encoding: utf-8

'''Drop down menus'''

from .utils import getPageText, installImage, createFolderWithOptionalDefaultPageView
from plone.api import content as pac
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer as ccic
from plone.portlet.static.static import Assignment as StaticPortletAssignment
from plone.portlets.interfaces import IPortletManager, IPortletAssignmentMapping
from plone.registry.interfaces import IRegistry
from zope.component import getUtility, getMultiAdapter
from zope.container.interfaces import INameChooser
import logging

_logger = logging.getLogger(__name__)


def installDataAndResources(context):
    u'''Set up the "Data and Resources" tab'''

    dataAndResources = createFolderWithOptionalDefaultPageView(
        context,
        'data-and-resources',
        u'Data and Resources',
        u'Scientific data, informatics tools, reference specimens, and more.',
        getPageText('dataAndResources')
    )

    for ident, fn, ct, title, desc in (
        ('biomarker-image', u'nci-dna.jpg', 'image/jpeg', u'Biomarker Image', u'DNA and other material representative of biomarkers.'),
        ('protocols-image', u'ferguson-protocol.jpg', 'image/jpeg', u'Protocols Image', u'A physician with a stethoscope and protective gloves.'),
        ('data-image', u'nci-vol-9792-72.jpg', 'image/jpeg', u'Science Data Image', u'A physician in front of a modern computing device.'),
        ('specimen-availability-image', u'reed-tubes.jpg', 'image/jpeg', u'Research Tools and Clinical Specimen Availability Image', u'The title says it all.'),
        ('informatics-image', u'monitors.jpg', 'image/jpeg', u'Informatics Tools Image', u'An abstract background representing data with computer monitors in the foreground.'),
        ('publications-image', u'emily-books.jpg', 'image/jpeg', u'Publications Image', u'An photograph of upright books, but not their spines—their opposite page sides instead.'),
    ):
        installImage(dataAndResources, fn, ident, title, desc, ct)

    # 👉 Okay, big moves:
    pac.move(source=pac.get('/biomarkers'), target=dataAndResources)
    pac.move(source=pac.get('/protocols'), target=dataAndResources)
    pac.move(source=pac.get('/data'), target=dataAndResources)
    pac.move(source=pac.get('/publications'), target=dataAndResources)
    pac.move(source=pac.get('/informatics'), target=dataAndResources)
    # pac.move(source=pac.get('/resources/sample-reference-sets'), target=dataAndResources)

    # During development, I'm just doing this instead of the above:
    # pac.delete(obj=pac.get('/biomarkers'), check_linkintegrity=False)
    # # pac.delete(obj=pac.get('/protocols'), check_linkintegrity=False)  # Can't delete this; causes error
    # # So for now, delete its contents and move its container
    # for item in pac.get('/protocols').values():
    #     pac.delete(obj=item, check_linkintegrity=False)
    # pac.move(source=pac.get('/protocols'), target=dataAndResources)
    # pac.delete(obj=pac.get('/data'), check_linkintegrity=False)
    # pac.delete(obj=pac.get('/publications'), check_linkintegrity=False)
    # pac.delete(obj=pac.get('/resources/sample-reference-sets'), check_linkintegrity=False)  # Can't delete this either; error

    # HK wants LabCAS in a sub menu
    i = pac.get('/data-and-resources/informatics')
    f = createFolderWithOptionalDefaultPageView(i, 'labcas', u'LabCAS', u'Laboratory Catalog and Archive System')
    pac.move(source=pac.get('/resources/edrnLabCASUserGuide31081716118.pdf'), target=f)
    pac.move(source=pac.get('/resources/core_labcasmetadataversion2.xlsx'), target=f)
    pac.move(source=pac.get('/resources/LabCASAPIs.pdf'), target=f)

    # HK wants a tools folder
    f = createFolderWithOptionalDefaultPageView(i, 'tools', u'Informatics Tools', u'Utilities for cancer informatics.')
    pac.move(source=pac.get('/resources/secretome'), target=f)
    pac.move(source=pac.get('/resources/microrna'), target=f)


def installWorkWithEDRN(context, archive):
    '''Set up the "Work with EDRN" tab'''
    workWithEDRN = createFolderWithOptionalDefaultPageView(
        context,
        'work-with-edrn',
        u'Work with EDRN',
        u'Cooperative and collaborative opportunities, funding opportunities, studies, and more.',
        getPageText('workWithEDRN')
    )
    createFolderWithOptionalDefaultPageView(
        workWithEDRN,
        'associate-membership-program',
        u'Associate Membership Program',
        u'Please note: the EDRN is suspending the acceptance of applications for Associate Membership categories A and B until further notice. Associate Membership applications category C are still accepted.',
        getPageText('associateMembershipProgram')
    )
    createFolderWithOptionalDefaultPageView(
        workWithEDRN,
        'validation-study-proposals',
        u'Propose a Validation Study',
        u'Describes the steps necessary to propose a validation study.',
        getPageText('validatinStudyProposals')
    )
    pac.move(source=pac.get('/colops/faq'), target=workWithEDRN)
    pac.move(source=pac.get('/colops/image.gif'), target=workWithEDRN)
    pac.move(source=pac.get('/colops/assoc'), target=archive)
    pac.move(source=pac.get('/colops/vsp'), target=archive)

    # But we need to split out the 'private' part of the existing 'advocates' page
    pubPriv = createFolderWithOptionalDefaultPageView(
        workWithEDRN,
        'public-private-partnerships',
        u'Public-Private Partnerships',
        u'Guidelines and existing partnerships with public and private entities.',
    )
    for path in (
        '/advocates/edrn-ip.pdf',
        '/colops/edrn-ppp-guidelines',
    ):
        obj = pac.get(path)
        pac.move(source=obj, target=pubPriv)
    advocacy = createFolderWithOptionalDefaultPageView(
        workWithEDRN,
        'advocacy-groups',
        u'Advocacy Groups',
        u'Information for cancer patients and their advocates.',
        getPageText('advocacyGroups')
    )
    pac.move(source=pac.get('/advocates/edrn-research-highlights'), target=advocacy)

    pac.delete(obj=pac.get('/advocates'))


def installNewsAndEvents(context):
    '''News and events menu'''
    newsAndEvents = createFolderWithOptionalDefaultPageView(
        context,
        'news-and-events',
        u'News and Events',
        u'Announcements, noteworthy information, and occasions (both special and otherwise) for EDRN.',
        getPageText('newsAndEvents')
    )
    # Collect the newsletters
    newsletters = createFolderWithOptionalDefaultPageView(
        newsAndEvents,
        'newsletters',
        u'EDRN Newsletter',
        u'A bulletin issued periodically to the members of and anyone interested in EDRN.'
    )
    # So we need to edit the page with them and remove their hyperlinks
    bookshelfView = pac.get('/docs/index_html')
    bookshelfView.text = RichTextValue(getPageText('bookshelf'), 'text/html', 'text/x-html-safe')
    for i in (
        'EDRNeNewsletters.pdf',
        'EDRNeNewslettersJune2018.pdf',
        'enewsletter-august-2018',
        'enewsletter-october-2018',
        'EDRNeNewslettersDecember32018FINAL.pdf',
        'edrn-enewsletter-february-2019',
        'edrn-enewsletter-march-2019',
        'edrn-enewsletter-april-2019',
    ):
        obj = pac.get('/docs/' + i)
        if not obj: import pdb;pdb.set_trace()
        pac.move(source=obj, target=newsletters)

    # Add the "Prevention Science blogs"
    createFolderWithOptionalDefaultPageView(
        newsAndEvents,
        'prevention-science-blogs',
        u'Prevention Science blogs',
        u'A research blog published by the Division of Cancer Prevention.',
        getPageText('preventionScienceBlog')
    )

    # Meeting registration
    createFolderWithOptionalDefaultPageView(
        newsAndEvents,
        'meeting-registration',
        u'Meeting Registration',
        u'How to register for and details about upcoming EDRN meetings.',
        getPageText('meetingRegistration')
    )

    # Past meetings
    past = createFolderWithOptionalDefaultPageView(
        newsAndEvents,
        'meeting-reports',
        u'Meeting Reports',
        u'Reports generated from EDRN meetings in the past.',
        getPageText('meetingReports')
    )
    pac.move(source=pac.get('/cancer-bioinformatics-workshop'), target=past)


def installAboutEDRN(portal):
    '''…'''
    about = createFolderWithOptionalDefaultPageView(
        portal,
        'about',
        u'About EDRN',
        u'All about the Early Detection Research Network.',
        getPageText('about')
    )
    portlet = StaticPortletAssignment(
        header=u'Organization',
        text=RichTextValue(getPageText('aboutPortlet'), 'text/html', 'text/html'),
        omit_border=False
    )
    manager = getUtility(IPortletManager, u'plone.leftcolumn')
    mapping = getMultiAdapter((about, manager), IPortletAssignmentMapping)
    chooser = INameChooser(mapping)
    mapping[chooser.chooseName(None, portlet)] = portlet

    installImage(
        about, u'org-chart.png', 'org-chart.png', u'Organizational Chart',
        u'A chart depicting the organizational structure of the Early Detection Research Network.', 'image/png'
    )

    pac.move(source=pac.get('/resources/highlights'), target=about)
    pac.move(source=pac.get('/sites'), target=about)
    pac.move(source=pac.get('/members-list'), target=about)
    pac.move(source=pac.get('/groups'), target=about)

    # Somthing misfiled from the bookshelf
    pac.move(
        source=pac.get('/docs/edrn-pancreas-working-group-meeting'),
        target=pac.get('/about/groups/g-i-and-other-associated-cancers-research-group')
    )


def install(portal):
    # First, turn on; activate drop-down menus by setting a depth > 1
    registry = getUtility(IRegistry)
    registry['plone.navigation_depth'] = 3

    # First pass: archive old stuff
    from .content_reorg import archiveStuff, archiveBookshelf
    archive = archiveStuff(portal)

    installDataAndResources(portal)
    installWorkWithEDRN(portal, archive)
    installNewsAndEvents(portal)
    installAboutEDRN(portal)

    pac.move(source=pac.get('/colops'), target=archive)

    # Drop out! Fix the new ingest paths
    registry['eke.knowledge.interfaces.IPanel.objects'] = [
        u'resources/body-systems', u'resources/diseases', u'resources/miscellaneous-resources',
        u'data-and-resources/publications',
        u'about/sites',
        u'data-and-resources/protocols',
        u'data-and-resources/data',
        u'data-and-resources/biomarkers',
        u'about/groups'
    ]

    archiveBookshelf(portal, archive)

    # Misc cleanup
    resources = pac.get('/resources')
    resources.exclude_from_nav = True
    resources.reindexObject()
    about = pac.get('/about-edrn')
    about.exclude_from_nav = True
    about.reindexObject()
