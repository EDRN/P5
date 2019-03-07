# encoding: utf-8

from . import _, dublincore
from .person import IPerson
from Acquisition import aq_inner
from five import grok
from knowledgeobject import IKnowledgeObject
from zope import schema


# Pre-declared so that the "sponsor" field works, see below.
class ISite(IKnowledgeObject):
    pass


class ISite(IKnowledgeObject):
    '''Site.'''
    abbreviation = schema.TextLine(
        title=_(u'Abbreviation'),
        description=_(u'A short name for the site.'),
        required=False,
    )
    sponsor = schema.Object(
        title=_(u'Sponsoring Site'),
        description=_(u"What site, if any, that sponsors this site's membership in EDRN."),
        required=False,
        schema=ISite  # Requires ISite already declared, see above.
    )
    fundingStartDate = schema.TextLine(
        title=_(u'Funding Start Date'),
        description=_(u'When funding for this site started.'),
        required=False,
    )
    fundingEndDate = schema.TextLine(
        title=_(u'Funding End Date'),
        description=_(u'When funding for this site stopped.'),
        required=False,
    )
    fwaNumber = schema.TextLine(
        title=_(u'FWA Number'),
        description=_(u'The so-called "FWA" number assigned to this site.'),
        required=False,
    )
    specialty = schema.TextLine(
        title=_(u'specialty'),
        description=_(u'What this site is really good at.'),
        required=False,
    )
    homePage = schema.TextLine(
        title=_(u'Home Page'),
        description=_(u"URL to the site's \"home page\" on the new Inter-Net phenomenon known as WWW or World Wide Webb. NOTE:" \
            + " Requires NCSA Mosaic or Inter-Net eXplorer."),
        required=False,
    )
    memberType = schema.TextLine(
        title=_(u'Member Type'),
        description=_(u'What particular kind of member site this is.'),
        required=False,
    )
    historicalNotes = schema.Text(
        title=_(u'Historical Notes'),
        description=_(u'Various notes made by various individuals within EDRN about this EDRN site.'),
        required=False,
    )
    principalInvestigator = schema.Object(
        title=_(u'Principal Investigator'),
        description=_(u'The leading investigator leading EDRN research at this site.'),
        required=False,
        schema=IPerson
    )
    # coPrincipalInvestigators = schema.List(
    #     title=_(u'Co-Principal Investigators'),
    #     description=_(u'Additional leading principal investigators.'),
    #     required=False,
    #     value_type=schema.Object(
    #         title=_(u'Co-Principal Investigator'),
    #         description=_(u'Additional leading principal investigator.'),
    #         schema=IPerson
    #     )
    # )
    # coInvestigators = schema.List(
    #     title=_(u'Co-Investigators'),
    #     description=_(u'Assistant or associate investigators helping out with EDRN research at the site.'),
    #     required=False,
    #     value_type=schema.Object(
    #         title=_(u'Co-Investigator'),
    #         description=_(u'Assistant or associate investigator helping out.'),
    #         schema=IPerson
    #     )
    # )
    # investigators = schema.List(
    #     title=_(u'Investigators'),
    #     description=_(u'Investigators at the site conducting other research.'),
    #     required=False,
    #     value_type=schema.Object(
    #         title=_(u'Investigator'),
    #         description=_(u'Investigator at the site conducting other research.'),
    #         schema=IPerson
    #     )
    # )

    # No longer neeed:
    # piUID = schema.TextLine(
    #     title=_(u'PI UID'),
    #     description=_(u'Unique identifier of the principal investigator.'),
    #     required=False,
    # )

    siteID = schema.TextLine(
        title=_(u'Site ID'),
        description=_(u'DMCC-assigned identifier of the site.'),
        required=False,
    )
    organs = schema.List(
        title=_(u'Organs'),
        description=_(u'Names of the organs on which this site focuses.'),
        required=False,
        value_type=schema.TextLine(
            title=_(u'Organ'),
            description=_(u'Names of an organ on which this site focuses.'),
        )
    )
    proposal = schema.Text(
        title=_(u'Proposal'),
        description=_(u'Title of the proposal that produced this site (for BDLs only).'),
        required=False,
    )
    piObjectID = schema.TextLine(
        title=_(u'PI Object ID'),
        description=_(u'Object identifier of the principal investigator.'),
        required=False,
    )
    piName = schema.TextLine(
        title=_(u'PI Name'),
        description=_(u'Name of the principal investigator.'),
        required=False,
    )


ISite.setTaggedValue('predicates', {
    dublincore.TITLE_URI: ('title', False),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#abstract': ('description', False),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#abbrevName': ('abbreviation', False),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#fundStart': ('fundingStartDate', False),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#fundEnd': ('fundingEndDate', False),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#fwa': ('fwaNumber', False),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#program': ('specialty', False),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#url': ('homePage', False),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#memberType': ('memberType', False),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#historicalNotes': ('historicalNotes', False),
    # Handled specially in SiteFolderIngest.ingest:
    # u'http://edrn.nci.nih.gov/rdf/schema.rdf#pi': ('principalInvestigator', True),
    # u'http://edrn.nci.nih.gov/rdf/schema.rdf#copi': ('coPrincipalInvestigators', True),
    # u'http://edrn.nci.nih.gov/rdf/schema.rdf#coi': ('coInvestigators', True),
    # u'http://edrn.nci.nih.gov/rdf/schema.rdf#investigator': ('investigators', True),
    u'http://edrn.nci.nih.gov/rdf/schema.rdf#organ': ('organs', False)
})
ISite.setTaggedValue('fti', 'eke.knowledge.site')
ISite.setTaggedValue('typeURI', u'http://edrn.nci.nih.gov/rdf/types.rdf#Site')


class View(grok.View):
    grok.context(ISite)
    grok.require('zope2.View')
    def showSponsor(self):
        context = aq_inner(self.context)
        memberType = context.memberType
        if not memberType: return False
        memberType = memberType.strip()
        return memberType.startswith(u'Associate') or memberType.startswith('Assocaite')  # Thanks DMCC. Ugh >.<
