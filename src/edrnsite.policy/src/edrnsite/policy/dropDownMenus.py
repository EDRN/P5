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
    return pkg_resources.resource_stream(__name__, os.path.join('content', 'pages', name + '.html')).read()


def _createFolderWithDefaultPageView(context, ident, title, desc, body=None):
    '''Create a Folder with object identifier ``ident`` and title ``title`` as well as description
    ``desc`` in the ``context`` object. If ``body`` is not None, then also create a Page in the
    Folder with the same title and description and the given ``body`` text, and make the Page the
    default view of the folder.
    '''
    if ident in context.keys(): context.manage_delObjects([ident])
    folder = ccic(context, 'Folder', id=ident, title=title, description=desc)
    body = RichTextValue(body,  'text/html', 'text/x-html-safe')
    if body:
        page = ccic(folder, 'Document', id=ident, title=title, description=desc, body=body)
        folder.setDefaultPage(page.id)
    publish(folder)
    return folder


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

    # First tab: "Data and Resources"

    dataAndResources = _createFolderWithDefaultPageView(
        portal,
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

    # Second tab: "Work with EDRN"
    workWithEDRN = _createFolderWithDefaultPageView(
        portal,
        'work-with-edrn',
        u'Work with EDRN',
        u'Cooperative and collaborative opportunities, funding opportunities, studies, and more.',
        _getPageText('workWithEDRN')
    )
    _createFolderWithDefaultPageView(
        workWithEDRN,
        'associate-membership-program',
        u'Associate Membership Program',
        u'Please note: the EDRN is suspending the acceptance of applications for Associate Membership categories A and B until further notice. Associate Membership applications category C are still accepted.',
        _getPageText('associateMembershipProgram')
    )
    _createFolderWithDefaultPageView(
        workWithEDRN,
        'validation-study-proposals',
        u'Propose a Validation Study',
        u'Describes the steps necessary to propose a validation study.',
        _getPageText('validatinStudyProposals')
    )
    ### pac.delete(obj=pac.get('/colops/assoc'))
    ### pac.delete(obj=pac.get('/colops/vsp'))

    # But we need to split out the 'private' part of the existing 'advocates' page
    pubPriv = _createFolderWithDefaultPageView(
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
        if not obj: import pdb;pdb.set_trace()
        pac.move(source=obj, target=pubPriv)
    advocacy = _createFolderWithDefaultPageView(
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

    ### pac.delete(obj=pac.get('/colops'))

    # Drop down! We're done
