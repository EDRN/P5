# encoding: utf-8

'''Drop down menus'''


from plone.api import content as pac
from plone.dexterity.utils import createContentInContainer as ccic


_danReview = u' 🚀 Dan, please review; dan.crichton@jpl.nasa.gov.'
_christosReview = u' 🔬 Christos, please review; patriotisc@mail.nih.gov.'


def archiveStuff(portal):
    archiveFolder = ccic(portal, 'Folder', id='archive', title=u'Archive', description=u'Archived Items')
    archiveFolder.exclude_from_nav = True

    def archive(path):
        pac.move(source=pac.get(path), target=archiveFolder)

    def delete(path):
        pac.delete(obj=pac.get(path), check_linkintegrity=False)

    archive('/colops/china-edrn')
    archive('/funding-opportunities')

    # Move, then rename this and ask Christos
    archive('/colops/2002amapplication.pdf')
    pac.rename(obj=pac.get('/archive/2002amapplication.pdf'), new_id='part-1-edrn-application-for-associate-membership')
    typographicallyPoorForm = pac.get('/archive/part-1-edrn-application-for-associate-membership')
    typographicallyPoorForm.title = u'Part 1 of the EDRN Application for Associate Membership'
    typographicallyPoorForm.description = typographicallyPoorForm.description + _christosReview
    typographicallyPoorForm.reindexObject()
    archive('/resources/standard-operating-procedures')
    archive('/about-edrn/objectives')
    objectives = pac.get('/archive/objectives')
    objectives.description = objectives.description + _christosReview
    objectives.reindexObject()
    archive('/about-edrn/scicomponents')
    scicomps = pac.get('/archive/scicomponents')
    scicomps.description = scicomps.description + _christosReview
    scicomps.reindexObject()

    # Nuke this
    delete('/resources/protocols')

    # Dan needs to review
    archive('/resources/edrn-knowledge-environment.pdf')
    coolPoster = pac.get('/archive/edrn-knowledge-environment.pdf')
    coolPoster.description = coolPoster.description + _danReview
    coolPoster.reindexObject()

    # Heather wants this saved for Dan to review for some reason
    archive('/resources/erne')
    erne = pac.get('/archive/erne')
    erne.description = erne.description + u'; Please note: this link is *broken* but HK wants it saved for Dan to confirm.' + _danReview
    erne.reindexObject()

    # Simple moves
    archive('/resources/specimens')
    archive('/resources/informatics-faq')
    archive('/resources/edrnLabCASUserGuide31081714326.pdf')
    archive('/resources/hybridomas-for-pancreatic-cancer-biomarkers')
    archive('/resources/labcas-documentation')
    archive('/resources/grant-numbers')  # Can't simply delete since /resources default view linsk to it
    archive('/about-edrn/photos')  # Can't delete; causes stack trace
    archive('/about-edrn/edrn-pre-applications-webinar-2014/')
    archive('/about-edrn/edrn_manualofoperations_4.0.pdf')  # Can't delete, causes stack trace
    archive('/about-edrn/appendix-9-2014-secure-website-users-guide')
    archive('/advocates/EDRNPatientAdvocateWebinar9-22-2011vHandout.pdf')
    archive('/advocates/EDRN_Pt_AdvocateWebinar9222011.mp4')
    archive('/advocates/mou-canary-foundation.pdf')
    archive('/advocates/31003_turkishministryofhealth_nci_mou.pdf')
    archive('/advocates/edrn-lung-collaborative-group-webinar-handouts')
    archive('/advocates/webinars')
    archive('/advocates/investigator-of-the-month')
    archive('/advocates/frequently-asked-questions')  # Can't delete, causes stack trace
    archive('/advocates/MOU Shanghai Center for Bioinformation Technology.pdf')
    archive('/advocates/lustgarten.pdf')
    archive('/advocates/mou-with-beijing-youan-hospital')
    archive('/advocates/loi-with-beijing-tiantan-hospital')
    archive('/advocates/EDRN webinar 6 24.pdf')
    archive('/advocates/EDRN Webinar Feb 2015.pdf')
    archive('/advocates/EDRNBDLApplicantOrientationMeetingApril212016.pdf')
    archive('/advocates/Martin Sanda webinar.pdf')
    archive('/advocates/EDRN Webinar Sep 2014.pdf')
    archive('/advocates/EDRN webinar May 2014.pdf')
    archive('/advocates/EDRN Webinar Feb 2014.pdf')
    archive('/advocates/prostate-collaborative-group-handouts')
    archive('/advocates/newsletter-collection')  # Can't delete, causes stack trace

    # Simple deletions
    delete('/resources/edrnlabcasuserguide02061713408.pdf')
    delete('/about-edrn/edrn-mo-v3-1-0.pdf')
    delete('/advocates/tumor')
    delete('/advocates/proteomics')
    delete('/advocates/pubreq')
    delete('/advocates/press-releases')

    # That's it for now
    return archiveFolder


def archiveBookshelf(portal, archiveFolder):
    # The Bookshelf: we move specific items out but the rest goes right into the archive

    def archive(path):
        pac.move(source=pac.get(path), target=archiveFolder)

    # Misfiled
    pac.move(source=pac.get('/docs/EDRN5.pdf'), target=pac.get('/docs'))

    # Delete with prejudice
    archive('/docs/news-and-press-releases')  # Except we can't delete this; causes stack trace
    pac.delete(obj=pac.get('/docs/EDRNStrategicPlan.pdf'), check_linkintegrity=False)

    # And then the whole folder
    archive('/docs')
