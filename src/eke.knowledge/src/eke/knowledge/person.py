
# encoding: utf-8

from . import _
from .publication import IPublication
from Acquisition import aq_inner
from five import grok
from knowledgeobject import IKnowledgeObject
from zope import schema
import plone.api, urlparse


class IPerson(IKnowledgeObject):
    u'''Person.'''
    salutation = schema.TextLine(
        title=_(u'Saluation'),
        description=_(u'Words used to address the person.'),
        required=False,
    )
    givenName = schema.TextLine(
        title=_(u'Given Name'),
        description=_(u'The name given to the person at birth and is usually considered the "first" name in Western societies.'),
        required=False,
    )
    middleName = schema.TextLine(
        title=_(u'Middle Name'),
        description=_(u'A secondary name given the person.'),
        required=False,
    )
    surname = schema.TextLine(
        title=_(u'Surname'),
        description=_(u'The family name often inherited from birth parents and considered the "last" name in Western societies'),
        required=True,
    )
    phone = schema.TextLine(
        title=_(u'Telephone Number'),
        description=_(u'The number at which the person may be reached via the Public Switched Telephone Network.'),
        required=False,
    )
    fax = schema.TextLine(
        title=_(u'FAX'),
        description=_(u'Facsimile telephone number.'),
        required=False,
    )
    edrnTitle = schema.TextLine(
        title=_(u'EDRN Title'),
        description=_(u'Title or honorific given by the Early Detection Research Network.'),
        required=False,
    )
    specialty = schema.TextLine(
        title=_(u'Specialty'),
        description=_(u'Area of specialization taken by this person.'),
        required=False,
    )
    mbox = schema.TextLine(
        title=_(u'Mail Box Address'),
        description=_(u'The address at which the person may receive electronic mail.'),
        required=False,
    )
    mailingAddress = schema.Text(
        title=_(u'Mailing Address'),
        description=_(u'The postal address to which mail may be sent.'),
        required=False,
    )
    physicalAddress = schema.Text(
        title=_(u'Physical Address'),
        description=_(u'The address where the person is.'),
        required=False,
    )
    shippingAddress = schema.Text(
        title=_(u'Shipping Address'),
        description=_(u'The address where parcels destined for the person may be sent.'),
        required=False,
    )
    investigatorStatus = schema.TextLine(
        title=_(u'Investigator'),
        description=_(u'Status of this person as an investigator or as a mere staff member.'),
        required=False,
    )
    memberType = schema.TextLine(
        title=_(u'Member Type'),
        description=_(u'What particular kind of member site this is.'),
        required=False,
    )
    siteName = schema.TextLine(
        title=_(u'Site Name'),
        description=_(u'Name of the site where this member works.'),
        required=False,
    )
    piUID = schema.TextLine(
        title=_(u'PI UID'),
        description=_(u'Unique identifier of the principal investigator of the site where this person works.'),
        required=False,
    )
    accountName = schema.TextLine(
        title=_(u'Account Name'),
        description=_(u'DMCC-assigned account username.'),
        required=False,
    )
    secureSiteRole = schema.TextLine(
        title=_(u'Secure Site Role'),
        description=_(u'What role this person plays at the EDRN Secure Site'),
        required=False,
    )
    degrees = schema.List(
        title=_(u'Degrees'),
        description=_(u'Academic degrees bestowed upon this person'),
        required=False,
        value_type=schema.TextLine(title=_(u'Degree'), description=_(u'Academic degree bestowed upon this person'))
    )


IPerson.setTaggedValue('predicates', {
})
IPerson.setTaggedValue('fti', 'eke.knowledge.site')
IPerson.setTaggedValue('typeURI', u'http://edrn.nci.nih.gov/rdf/types.rdf#Site')


class View(grok.View):
    grok.context(IPerson)
    grok.require('zope2.View')
    def protocols(self):
        return ([], [])
    def publications(self):
        context = aq_inner(self.context)
        catalog = plone.api.portal.get_tool('portal_catalog')
        results = catalog(
            object_provides=IPublication.__identifier__,
            siteID=context.siteID,
            sort_on='sortable_title'
        )
        publications = []
        for i in results:
            publications.append(i.getObject())  # Any reason we're waking up objects here?
        return publications
    def staffID(self):
        context = aq_inner(self.context)
        i = urlparse.urlparse(context.identifier).path.split(u'/')[-1]
        return i if i else u'?'
