# encoding: utf-8

'''Drop down menus'''


from .setuphandlers import publish
from plone.dexterity.utils import createContentInContainer as ccic
from plone.app.textfield.value import RichTextValue
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from plone.api import content as pac
import logging, pkg_resources, os.path

_logger = logging.getLogger(__name__)


def _getPageText(name):
    return pkg_resources.resource_stream(__name__, 'content/pages/' + name + '.html').read().decode('utf-8')


def _createFolderWithOptionalDefaultPageView(context, ident, title, desc, body=None):
    '''Create a Folder with object identifier ``ident`` and title ``title`` as well as description
    ``desc`` in the ``context`` object. If ``body`` is not None, then also create a Page in the
    Folder with the same title and description and the given ``body`` text, and make the Page the
    default view of the folder.
    '''
    if ident in context.keys(): context.manage_delObjects([ident])
    folder = ccic(context, 'Folder', id=ident, title=title, description=desc)
    if body:
        body = RichTextValue(body,  'text/html', 'text/x-html-safe')
        page = ccic(folder, 'Document', id=ident, title=title, description=desc, text=body)
        folder.setDefaultPage(page.id)
    else:
        folder.setLayout('summary_view')
    publish(folder)
    return folder


def installDataAndResources(context):
    u'''Set up the "Data and Resources" tab'''

    dataAndResources = _createFolderWithOptionalDefaultPageView(
        context,
        'data-and-resources',
        u'Data and Resources',
        u'Scientific data, informatics tools, reference specimens, and more.',
        _getPageText('dataAndResources')
    )
    pac.move(source=pac.get('/biomarkers'), target=dataAndResources)
    pac.move(source=pac.get('/protocols'), target=dataAndResources)
    pac.move(source=pac.get('/data'), target=dataAndResources)
    pac.move(source=pac.get('/publications'), target=dataAndResources)
    pac.move(source=pac.get('/informatics'), target=dataAndResources)
    pac.move(source=pac.get('/resources/sample-reference-sets'), target=dataAndResources)


def installWorkWithEDRN(context):
    '''Set up the "Work with EDRN" tab'''
    workWithEDRN = _createFolderWithOptionalDefaultPageView(
        context,
        'work-with-edrn',
        u'Work with EDRN',
        u'Cooperative and collaborative opportunities, funding opportunities, studies, and more.',
        _getPageText('workWithEDRN')
    )
    _createFolderWithOptionalDefaultPageView(
        workWithEDRN,
        'associate-membership-program',
        u'Associate Membership Program',
        u'Please note: the EDRN is suspending the acceptance of applications for Associate Membership categories A and B until further notice. Associate Membership applications category C are still accepted.',
        _getPageText('associateMembershipProgram')
    )
    _createFolderWithOptionalDefaultPageView(
        workWithEDRN,
        'validation-study-proposals',
        u'Propose a Validation Study',
        u'Describes the steps necessary to propose a validation study.',
        _getPageText('validatinStudyProposals')
    )
    ### pac.delete(obj=pac.get('/colops/assoc'))
    ### pac.delete(obj=pac.get('/colops/vsp'))

    # But we need to split out the 'private' part of the existing 'advocates' page
    pubPriv = _createFolderWithOptionalDefaultPageView(
        workWithEDRN,
        'public-private-partnerships',
        u'Public-Private Partnerships',
        u'Guidelines and existing partnerships with public and private entities.',
    )
    for path in (
        '/advocates/edrn-ip.pdf',
        '/colops/edrn-ppp-guidelines',
        '/advocates/mou-canary-foundation.pdf',
        '/advocates/31003_turkishministryofhealth_nci_mou.pdf',
        '/advocates/lustgarten.pdf',
        '/advocates/MOU Shanghai Center for Bioinformation Technology.pdf',
        '/advocates/mou-with-beijing-youan-hospital',
        '/advocates/loi-with-beijing-tiantan-hospital',
    ):
        obj = pac.get(path)
        pac.move(source=obj, target=pubPriv)
    advocacy = _createFolderWithOptionalDefaultPageView(
        workWithEDRN,
        'advocacy-groups',
        u'Advocacy Groups',
        u'Information for cancer patients and their advocates.',
        _getPageText('advocacyGroups')
    )
    pac.move(source=pac.get('/advocates/webinars'), target=advocacy)
    pac.move(source=pac.get('/advocates/frequently-asked-questions'), target=advocacy)
    pac.move(source=pac.get('/advocates/edrn-research-highlights'), target=advocacy)
    for i in (
        'EDRNBDLApplicantOrientationMeetingApril212016.pdf',
        'EDRN webinar 6 24.pdf',
        'EDRN Webinar Feb 2015.pdf',
        'EDRN Webinar Sep 2014.pdf',
        'EDRN webinar May 2014.pdf',
        'EDRN Webinar Feb 2014.pdf',
        'prostate-collaborative-group-handouts',
        'edrn-lung-collaborative-group-webinar-handouts',
        'EDRN_Pt_AdvocateWebinar9222011.mp4',
        'EDRNPatientAdvocateWebinar9-22-2011vHandout.pdf',
        'investigator-of-the-month',
        'newsletter-collection',
    ):
        obj = pac.get('/advocates/' + i)
        pac.move(source=obj, target=advocacy)

    pac.delete(obj=pac.get('/advocates'))


def installNewsAndEvents(context):
    '''News and events menu'''
    newsAndEvents = _createFolderWithOptionalDefaultPageView(
        context,
        'news-and-events',
        u'News and Events',
        u'Announcements, noteworthy information, and occasions (both special and otherwise) for EDRN.',
        _getPageText('newsAndEvents')
    )
    # Collect the newsletters
    newsletters = _createFolderWithOptionalDefaultPageView(
        newsAndEvents,
        'newsletters',
        u'EDRN Newsletter',
        u'A bulletin issued periodically to the members of and anyone interested in EDRN.'
    )
    # So we need to edit the page with them and remove their hyperlinks
    bookshelfView = pac.get('/docs/index_html')
    bookshelfView.text = RichTextValue(_getPageText('bookshelf'), 'text/html', 'text/x-html-safe')
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
    _createFolderWithOptionalDefaultPageView(
        newsAndEvents,
        'prevention-science-blogs',
        u'Prevention Science blogs',
        u'A research blog published by the Division of Cancer Prevention.',
        _getPageText('preventionScienceBlog')
    )


def install(portal):
    # First, turn on; activate drop-down menus by setting a depth > 1
    registry = getUtility(IRegistry)
    registry['plone.navigation_depth'] = 3

    # Now tune in; that is, rearrange the content so the menus work nicely.
    #
    # We'll need a dumping ground for stuff we don't know what to do with
    misc = ccic(
        portal, 'Folder', id='misc', title=u'Miscellaneous',
        description=u'Miscellaneous items that should go elsewhere.', exclude_from_nav=True
    )
    pac.move(source=pac.get('/colops/china-edrn'), target=misc)
    pac.move(source=pac.get('/funding-opportunities'), target=misc)

    installDataAndResources(portal)
    installWorkWithEDRN(portal)
    installNewsAndEvents(portal)

    ### pac.delete(obj=pac.get('/colops'))

    # Drop out! Fix the new ingest paths
    registry['eke.knowledge.interfaces.IPanel.objects'] = [
        u'resources/body-systems', u'resources/diseases', u'resources/miscellaneous-resources',
        u'data-and-resources/publications',
        u'sites',
        u'data-and-resources/protocols',
        u'data-and-resources/data',
        u'data-and-resources/biomarkers',
        u'groups'
    ]

    # Misc cleanup
    resources = pac.get('/resources')
    resources.exclude_from_nav = True
    resources.reindexObject()
    about = pac.get('/about-edrn')
    about.exclude_from_nav = True
    about.reindexObject()

