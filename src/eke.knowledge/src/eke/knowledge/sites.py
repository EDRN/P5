# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: sites and people.'''

from .bodysystems import Organ as BaseOrgan
from .constants import MAX_SLUG_LENGTH
from .knowledge import KnowledgeObject, KnowledgeFolder
from .publications import Publication
from .rdf import RDFAttribute, RelativeRDFAttribute
from .utils import edrn_schema_uri as esu
from .utils import Ingestor as BaseIngestor
from django.core.files.images import ImageFile
from django.db import models
from django.db.models.fields import Field
from django.db.models.functions import Lower
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.utils.text import slugify
from django_plotly_dash import DjangoDash
from eke.geocoding.models import InvestigatorAddress
from eke.geocoding.utils import get_addresses
from modelcluster.fields import ParentalKey
from modelcluster.fields import ParentalManyToManyField
from plotly.express import scatter_mapbox
from rdflib import URIRef
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlopen
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField
from wagtail.images.models import Image
from wagtail.models import Orderable, Page
from wagtail.search import index
import dash_core_components as dcc
import dash_html_components as html
import pandas, logging, rdflib, tempfile, libgravatar


_logger                     = logging.getLogger(__name__)
_siteType                   = 'http://edrn.nci.nih.gov/rdf/types.rdf#Site'
_internalIDPredicate        = 'urn:internal:id'
_interalProposalPredicate   = 'urn:internal:propsoal'
_internalOrganPredicate     = 'urn:internal:organ'
_surname_predicate_uri      = rdflib.URIRef('http://xmlns.com/foaf/0.1/surname')
_default_person_icon        = 'mp'


def get_predicate_value(uri: rdflib.URIRef, predicates: dict) -> str:
    return str(predicates[uri][0]) if uri in predicates else ''


class _MemberTypeRDFAttribute(RDFAttribute):
    def compute_new_value(self, modelField: Field, value: str, predicates: dict) -> object:
        if value.startswith('Associate Member C') or value.startswith('Assocaite Member C'):
            # Thanks DMCC
            value = 'Associate Member C'
        elif value.startswith('Associate Member B'):
            value = 'Associate Member B'
        elif value == 'Biomarker Developmental  Laboratories':
            # Thanks DMCC
            value = 'Biomarker Developmental Laboratories'
        elif value == 'SPORE':
            # CA-697
            value = 'SPOREs'
        return super().compute_new_value(modelField, value, predicates)


class _MailtoRemovingRDFAttribute(RDFAttribute):
    def compute_new_value(self, modelField: Field, value: str, predicates: dict) -> object:
        if value.startswith('mailto:'):
            value = value[7:]
        # Thanks DMCC
        garbage = {
            'kwriston': '',                                                          # 3518
            'smarquis@medicine.washington,edu': 'smarquis@medicine.washington.edu',  # 3039
            'jo&#39;leary@northshore.org': 'joe.leary@northshore.org',               # 2606
            'n/a': '',                                                               # 3664, 3663
            'tbd': '',                                                               # 3306
            'rebeccacmiller': '',                                                    # 3520
            'wgosbee@mdanderson': 'wgosbee@mdanderson.org',                          # 1347
            'nicole.capriotti@fccc,edu': 'nicole.capriotti@fccc.edu',                # 2472
            'bmccreedy@metabolon': 'bmccreedy@metabolon.com',                        # 2170
            'boevetj': '',                                                           # 3523
        }
        value = garbage.get(value, value)
        return super().compute_new_value(modelField, value, predicates)


class _ImageIngestingRDFAttribute(RDFAttribute):
    '''Special RDF attribute that handles URLs to images.'''
    
    def _get_file_name(self, url: str) -> str:
        '''Compute the file name from the given url.'''
        return urlparse(url).path.split('/')[-1]

    def _get_surname(self, predicates: dict) -> str:
        name = str(predicates.get(_surname_predicate_uri, [''])[0])
        if not name:
            name = str(predicates.get(rdflib.term.URIRef('urn:internal:id'), [''])[0])
            if not name:
                name = '«unknown»'
        return name

    def compute_new_value(self, modelField: Field, value: str, predicates: dict) -> object:
        # Curiously, we can't pass a URL stream to ImageFile, since Django's ImageFile expects
        # to be able to do seek() operations on it. So we have to download to a temporary file:
        name = self._get_surname(predicates)
        try:
            with tempfile.TemporaryFile() as out_file:
                with urlopen(value) as image_stream:
                    out_file.write(image_stream.read())
                image_file = ImageFile(out_file, name=self._get_file_name(value))
                image = Image(
                    title=f'Photo of {name}', file=image_file,
                    # These values only make sense for the photos from the DMCC:
                    focal_point_x=66, focal_point_y=52, focal_point_height=76, focal_point_width=57
                )
                image.save()
            return image
        except HTTPError:
            _logger.warning('😡 The URL to image «%s» is invalid', value)
            return None


class Site(KnowledgeObject):
    template = 'eke.knowledge/site.html'
    parent_page_types = ['ekeknowledge.SiteIndex']
    subpage_types = ['ekeknowledge.Person']
    preview_modes = []
    abbreviation = models.CharField(max_length=40, blank=True, null=False, help_text='A short name for the site')
    fundingStartDate = models.CharField(max_length=25, blank=True, null=False, help_text='When money was first given')
    fundingEndDate = models.CharField(max_length=25, blank=True, null=False, help_text='When the money stopped flowing')
    dmccSiteID = models.CharField(max_length=10, blank=True, null=False, help_text='DMCC-assigned number of the site')
    memberType = models.CharField(max_length=80, blank=True, null=False, help_text='Kind of member site')
    homePage = models.URLField(blank=True, null=False, help_text="Uniform Resource Locator of site's home page")
    sponsor = models.ForeignKey(
        'self', null=True, blank=True, verbose_name='Sponsoring Site', related_name='sponsored_site',
        on_delete=models.SET_NULL
    )
    pi = models.ForeignKey(
        'ekeknowledge.Person', null=True, blank=True, verbose_name='Principal Investigator', related_name='site_i_lead',
        on_delete=models.SET_NULL
    )
    coPIs = ParentalManyToManyField(
        'ekeknowledge.Person', blank=True, verbose_name='Co-Prinicipal Investigators', related_name='site_i_co_lead',
    )
    coIs = ParentalManyToManyField(
        'ekeknowledge.Person', blank=True, verbose_name='Co-Investigators', related_name='site_i_co_investigate',
    )
    investigators = ParentalManyToManyField(
        'ekeknowledge.Person', blank=True, verbose_name='Investigators', related_name='site_i_investigate',
    )
    specialty = RichTextField(blank=True, null=False, help_text="What the site's really good at")
    proposal = models.CharField(
        blank=True, null=False, max_length=250, help_text='BDL-only proposal title that produced this site'
    )
    content_panels = KnowledgeObject.content_panels + [
        FieldPanel('abbreviation'),
        FieldPanel('fundingStartDate'),
        FieldPanel('fundingEndDate'),
        FieldPanel('dmccSiteID'),
        FieldPanel('homePage'),
        FieldPanel('sponsor'),
        FieldPanel('specialty'),
        FieldPanel('proposal'),
        InlinePanel('organs', label='Organs'),
        FieldPanel('pi'),
        FieldPanel('coPIs'),
        FieldPanel('coIs'),
        FieldPanel('investigators'),
    ]
    search_fields = KnowledgeObject.search_fields + [
        index.SearchField('abbreviation'),
        index.SearchField('dmccSiteID'),
        index.RelatedFields('organs', [index.SearchField('value')]),
    ]

    def _shouldSponsorBeShown(self):
        if not self.memberType: return False
        memberType = self.memberType.strip()
        potential = memberType.startswith('Associate') or memberType.startswith('Assocaite')  # Thanks DMCC
        sponsorAvailable = self.sponsor is not None
        return potential and sponsorAvailable

    def get_context(self, request: HttpRequest, *args, **kwargs) -> dict:
        context = super().get_context(request, *args, **kwargs)
        context['showSponsor'] = self._shouldSponsorBeShown()

        anointed = set()
        if self.pi: anointed.add(self.pi.identifier)
        for field in ('coPIs', 'coIs', 'investigators'):
            people = getattr(self, field, None)
            if people:
                anointed &= set([i for i in people.values_list('identifier', flat=True).distinct()])
        staff = Person.objects.child_of(self).exclude(identifier__in=anointed).live().public().order_by('title')
        context['staff'] = staff
        return context

    class Meta:
        # indexes = [models.Index(fields=['pubMedID']), models.Index(fields=['year'])]
        pass

    class RDFMeta:
        fields = {
            esu('abbrevName'): RDFAttribute('abbreviation', scalar=True),
            esu('fundStart'): RDFAttribute('fundingStartDate', scalar=True),
            esu('fundEnd'): RDFAttribute('fundingEndDate', scalar=True),
            _internalIDPredicate: RDFAttribute('dmccSiteID', scalar=True),
            esu('memberType'): _MemberTypeRDFAttribute('memberType', scalar=True),
            esu('url'): RDFAttribute('homePage', scalar=True),
            esu('sponsor'): RelativeRDFAttribute('sponsor', scalar=True),
            esu('program'): RDFAttribute('specialty', scalar=True),
            _interalProposalPredicate: RDFAttribute('proposal', scalar=True),
            _internalOrganPredicate: RDFAttribute('organs', scalar=False),
            # esu('year'): RDFAttribute('year', scalar=True, rel=False),
            # str(rdflib.DCTERMS.creator): RDFAttribute('authors', scalar=False, rel=False),
            **KnowledgeObject.RDFMeta.fields
        }


class SiteOrgan(BaseOrgan):
    '''Organs studied at a particular site.'''
    page = ParentalKey(Site, on_delete=models.CASCADE, related_name='organs')


class Person(KnowledgeObject):
    template = 'eke.knowledge/person.html'
    parent_page_types = [Site]
    edrnTitle = models.CharField(max_length=40, blank=True, null=False, help_text='Title bestowed from on high')
    degrees = models.CharField(max_length=40, blank=True, null=False, help_text='Academia')
    mbox = models.EmailField(blank=True, null=False, help_text='Email address')
    fax = models.CharField(max_length=40, blank=True, null=False, help_text='Who seriously uses fax?')
    account_name = models.CharField(max_length=32, blank=True, null=False, help_text='DMCC-assigned login identifier')
    personID = models.CharField(max_length=10, blank=True, null=False, help_text='Code assigned by DMCC')
    address = models.CharField(max_length=250, blank=True, null=False, help_text='Mailing street address')
    city = models.CharField(max_length=60, blank=True, null=False, help_text='Mailing city')
    state = models.CharField(max_length=60, blank=True, null=False, help_text='Mailing state or province')
    postal_code = models.CharField(max_length=20, blank=True, null=False, help_text='Mailing postal code')
    country = models.CharField(max_length=35, blank=True, null=False, help_text='Mailing country')
    lat = models.FloatField(blank=True, null=True, help_text='Latitude')
    lon = models.FloatField(blank=True, null=True, help_text='Longitude')
    photo = models.ForeignKey(
        'wagtailimages.Image', null=True, blank=True, on_delete=models.SET_NULL, related_name='person_photograph'
    )

    content_panels = KnowledgeObject.content_panels + [
        FieldPanel('edrnTitle'),
        FieldPanel('degrees'),
        FieldPanel('mbox'),
        FieldPanel('fax'),
        FieldPanel('personID'),
        FieldPanel('account_name'),
        FieldPanel('address'),
        FieldPanel('city'),
        FieldPanel('state'),
        FieldPanel('postal_code'),
        FieldPanel('country'),
        FieldPanel('photo'),
        FieldPanel('lat'),
        FieldPanel('lon'),
    ]
    class RDFMeta:
        fields = {
            esu('edrnTitle'): RDFAttribute('edrnTitle', scalar=True),
            'http://xmlns.com/foaf/0.1/accountName': RDFAttribute('account_name', scalar=True),
            'http://www.w3.org/2001/vcard-rdf/3.0#fax': RDFAttribute('fax', scalar=True),
            'http://xmlns.com/foaf/0.1/mbox': _MailtoRemovingRDFAttribute('mbox', scalar=True),
            'http://xmlns.com/foaf/0.1/img': _ImageIngestingRDFAttribute('photo', scalar=True),
            _internalIDPredicate: RDFAttribute('personID', scalar=True),
            esu('mailingAddress'): RDFAttribute('address', scalar=True),
            esu('mailingCity'): RDFAttribute('city', scalar=True),
            esu('mailingState'): RDFAttribute('state', scalar=True),
            esu('mailingPostalCode'): RDFAttribute('postal_code', scalar=True),
            esu('mailingCountry'): RDFAttribute('country', scalar=True),


            # We do not include the KnowledgeObject's base RDFMeta fields here because people in EDRN don't
            # use Dublin Core.
        }

    def _gravatar_url(self, size: int) -> str:
        g = libgravatar.Gravatar(self.mbox)
        return g.get_image(size, default=_default_person_icon)

    def large_gravatar_url(self) -> str:
        return self._gravatar_url(300)

    def small_gravatar_url(self) -> str:
        return self._gravatar_url(190)

    def get_context(self, request: HttpRequest, *args, **kwargs) -> dict:
        context = super().get_context(request, *args, **kwargs)
        if (request.user.is_staff or request.user.is_superuser) and self.account_name:
            context['account_name'] = self.account_name
        my_site = Site.objects.filter(pi=self).first()
        if my_site:
            from eke.knowledge.protocols import Protocol
            opened, closed = [], []
            protocols = Protocol.objects.filter(involvedInvestigatorSites=my_site).order_by(Lower('title'))
            for protocol in protocols:
                if protocol.finish_date: closed.append(protocol)
                else: opened.append(protocol)
            context['opened'], context['closed'] = opened, closed

            pubs = Publication.objects.filter(siteID=my_site.identifier).public().live().order_by(Lower('title'))
            context['publications'] = pubs
        return context


class OrganizationalGroup(Page):
    '''An organizational group in EDRN consisting of a name and related sites.'''
    content_panels = Page.content_panels + [InlinePanel('group_members', label='Group Members')]
    preview_modes = []
    def serve(self, request: HttpRequest) -> HttpResponse:
        '''Overridden because you don't ever visit these; they're more "structural".'''
        return HttpResponseRedirect(self.get_parent().url)


class Ingestor(BaseIngestor):
    '''Site ingestor.'''

    _degree_pred_uri_prefix = 'http://edrn.nci.nih.gov/rdf/schema.rdf#degree'
    _doNotRecreateFlag      = 'Former employee'
    _employmentPredicateURI = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#employmentActive')
    _givenNamePredicateURI  = rdflib.URIRef('http://xmlns.com/foaf/0.1/givenname')
    _member_site_pred_uri   = rdflib.URIRef('urn:edrn:predicates:member_site')
    _middleNamePredicateURI = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#middleName')
    _personType             = 'http://edrn.nci.nih.gov/rdf/types.rdf#Person'
    _piPredicateURI         = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#pi')
    _org_group_type         = 'urn:edrn:types:org_group'
    _siteURIPredicate       = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#site')
    _coPIPredicateURI       = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#copi')
    _coIPredicateURI        = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#coi')
    _iPredicateURI          = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#investigator')
    _api_fetch_size         = 20

    def _get_dmcc_code(self, uri: rdflib.URIRef) -> str:
        return urlparse(uri).path.split('/')[-1]

    def readRDF(self) -> dict:
        '''Read the RDF.

        In this subclass implementation, we "inject" an extra statement so we can set the computed
        DMCC-site ID as well as the specialty information that was hand-entered years ago by Heather
        Kincaid.
        '''
        self.statements = super().readRDF()
        for subj, preds in self.statements.items():
            typeURI = str(preds[rdflib.RDF.type][0])
            if typeURI not in (_siteType, self._personType): continue
            dmccCode = self._get_dmcc_code(subj)
            preds[URIRef(_internalIDPredicate)] = [dmccCode]
        return self.statements

    def create_person_title(self, predicates: dict) -> tuple:
        '''Return a suitable "Last, First" formal name plus a "First Last" casual name of the person described by
        the ``predicates``.

        These are the formal and casual names, used in the title of a person object (formal) and promoted search
        description (casual).
        '''
        def get_name_components() -> tuple:
            return (
                get_predicate_value(_surname_predicate_uri, predicates),
                get_predicate_value(self._givenNamePredicateURI, predicates),
                get_predicate_value(self._middleNamePredicateURI, predicates)
            )
        last, first, middle = get_name_components()
        given = first
        if not given:
            given = middle
        else:
            if middle:
                given += ' ' + middle
        if not given:
            formal = casual = last
        else:
            formal, casual = f'{last}, {given}', f'{given} {last}'
        formal, casual = formal.strip(), casual.strip()
        if not formal or formal == ',':
            formal = '«PERSON WITH NO NAME»'
        if not casual:
            casual = '«PERSON WITH NO NAME»'
        return formal, casual

    def assign_academic_degree(self, person: Person, predicates: dict):
        degrees = []
        for i in range(1, 4):
            degree = str(predicates.get(rdflib.URIRef(f'{self._degree_pred_uri_prefix}{i}'), [''])[0]).strip()
            if degree:
                degrees.append(degree)
        degrees = ', '.join(degrees)
        if degrees:
            person.degrees = degrees

    def create_person(self, sites, uri: str, predicates: dict) -> Person:
        # Previously we deleted only those that where ``child_of(site)`` but this doesn't account for
        # people who move to different sites. Also, we need to refresh all sites because to keep the
        # tree consistent.

        site_uri = str(predicates[self._siteURIPredicate][0])

        # Somehow one or both of these sites is a problem but I have no time to figure it out.
        # if site_uri in ('http://edrn.nci.nih.gov/data/sites/417', 'http://edrn.nci.nih.gov/data/sites/284'):
        #     maybe break point()

        existing = Person.objects.filter(identifier__exact=uri).first()
        if existing is not None:
            parent = existing.get_parent()
            existing.delete()
            parent.refresh_from_db()

        if str(predicates.get(self._employmentPredicateURI, ['unknown'])[0]) == self._doNotRecreateFlag:
            return None

        site = sites.filter(identifier__exact=site_uri).first()
        if not site:
            _logger.info('🤷‍♀️ Potentially new person %s has no site %s', uri, site_uri)
            return None

        title, casual = self.create_person_title(predicates)
        promotion = f'{casual} is a member of the Early Detection Research Network.'
        person = Person(title=title, identifier=uri, live=True, search_description=promotion)
        for predicateURI, values, in predicates.items():
            predicateURI = str(predicateURI)
            rdfAttribute = person.RDFMeta.fields.get(predicateURI)
            if rdfAttribute is None: continue
            modelField = person._meta.get_field(rdfAttribute.name)
            rdfAttribute.modify_field(person, values, modelField, predicates)
        self.assign_academic_degree(person, predicates)
        site.add_child(instance=person)
        person.save()

        return person

    def ingest_people(self):
        created, deleted = set(), set()
        for subject, predicates in self.filter_by_rdf_type(self.statements, rdflib.URIRef(self._personType)):
            siteURI = predicates.get(self._siteURIPredicate, [])
            if not siteURI:
                _logger.info('🤨 Person %s does not have a site; skipping', subject)
                continue
            siteURI = str(siteURI[0])
            results = Site.objects.filter(identifier__exact=str(siteURI))
            if results.count() == 0:
                _logger.info('🤨 Person %s has a site %s that is unknown; skipping', subject, siteURI)
                continue
            elif results.count() > 1:
                _logger.info('😮 Wow, person %s has %d sites but I guess that is ok', subject, results.count())
            person = self.create_person(results, str(subject), predicates)
            if person is None:
                deleted.add(subject)
            else:
                created.add(person)
        return created, frozenset(), deleted

    def add_investigators(
        self, site: Site, predicate: rdflib.URIRef, predicates: dict, field_name: str, scalar: bool
    ):
        peopleURIs = [str(i) for i in predicates.get(predicate, [])]
        if not peopleURIs: return
        people = Person.objects.child_of(site).filter(identifier__in=peopleURIs)
        if people.count() == 0: return
        if scalar:
            setattr(site, field_name, people[0])
        else:
            getattr(site, field_name).set(people, clear=True)

    def setup_investigators(self):
        for subject, predicates in self.statements.items():
            typeURI = str(predicates[rdflib.RDF.type][0])
            if typeURI != _siteType: continue
            site = Site.objects.child_of(self.folder).filter(identifier=subject).first()
            if not site: continue
            self.add_investigators(site, self._piPredicateURI,   predicates, 'pi',            scalar=True)
            self.add_investigators(site, self._coPIPredicateURI, predicates, 'coPIs',         scalar=False)
            self.add_investigators(site, self._coIPredicateURI,  predicates, 'coIs',          scalar=False)
            self.add_investigators(site, self._iPredicateURI,    predicates, 'investigators', scalar=False)
            site.save()

    def setup_coordinates(self, people: set):
        misses, lookups = {}, set()

        # Assign coordinates for people for whom we've already got coordinates saved
        while len(people) > 0:
            p = people.pop()
            address = InvestigatorAddress.normalize(p.address, p.city, p.state, p.postal_code, p.country)
            if address is None: continue  # This person will never have a coordinate
            ia = InvestigatorAddress.objects.filter(address=address).first()
            if ia:
                p.lat, p.lon = ia.lat, ia.lon
                p.save()
            else:
                missed_people = misses.get(address, [])
                missed_people.append(p)
                misses[address] = missed_people
                lookups.add(address)

        # Now see if we can load more coordinates into the cache while updating the missing people
        def divvy(𝐋: list) -> list:
            while len(𝐋) > 0:
                group, 𝐋 = 𝐋[:self._api_fetch_size], 𝐋[self._api_fetch_size:]
                yield group

        _logger.debug('There are %d lat/lon addresses to look up', len(lookups))

        for group in divvy(list(lookups)):
            results = get_addresses(group)
            for addr, ia in results:
                for p in misses[addr]:
                    p.lat, p.lon = ia.lat, ia.lon
                    p.save()

    def getSlug(self, uri: rdflib.URIRef, predicates: dict) -> str:
        '''From the given ``predicates`` descibing a single object, figure out a good slug for it. By default,
        we return ``None`` which lets Wagtail figure out the right slug. Subclasses can override this and make
        a custom slug if needed.
        '''
        try:
            code, title = self._get_dmcc_code(uri), predicates[rdflib.DCTERMS.title][0]
            return slugify(f'{code} {title.strip()}')[:MAX_SLUG_LENGTH]
        except (IndexError, KeyError):
            return None

    def promote_sites(self, sites: set):
        '''Set up search descriptions for the newly created sites in ``sites``.'''
        for site in sites:
            promotion = f'{site.title} is a site belonging to the Early Detection Research Network.'
            site.search_description = promotion
            site.save()

    def record_organizational_groups(self):
        # Start with a clean slate
        OrganizationalGroup.objects.child_of(self.folder).delete()
        self.folder.refresh_from_db()
        for subject, predicates in self.filter_by_rdf_type(self.statements, rdflib.URIRef(self._org_group_type)):
            og = OrganizationalGroup(title=str(predicates[rdflib.DCTERMS.title][0]))
            self.folder.add_child(instance=og)
            og.save()
            for ms_uri in predicates.get(self._member_site_pred_uri, []):
                ms_preds = self.statements.get(ms_uri)
                if not ms_preds: continue
                ms = _create_org_group_member(ms_preds)
                if not ms:
                    _logger.error('Could not find needed info to make member group for %s; skipping', ms_uri)
                    continue
                og.group_members.add(ms)
                ms.save()

    def ingest(self):
        # We do this twice because the first time, sites that sponsor other sites may not yet exist. So the second
        # round links them up.
        c0, u0, d0 = super().ingest()      # This sets self.statements
        c1, u1, d1 = super().ingest()  
        c2, u2, d2 = self.ingest_people()  # So subseqeunt invocations like this one can use it
        self.setup_investigators()
        self.setup_coordinates(c2)
        self.promote_sites(c0 | c1)
        self.record_organizational_groups()
        return c0 | c1 | c2, u0 | u1 | u2, d0 | d1 | d2
        # return set(), set(), set()


class SiteIndex(KnowledgeFolder):
    '''A site index is a container for Sites.'''

    _bcc               = 'Biomarker Characterization Center'
    _bdl               = 'Biomarker Developmental Laboratories'
    _brl               = 'Biomarker Reference Laboratories'
    _cvc               = 'Clinical Validation Center'
    _dmcc              = 'Data Management and Coordinating Center'
    _ic                = 'Informatics Center'
    _nci               = 'National Cancer Institute'
    _typeA             = 'Associate Member A - EDRN Funded'
    _typeB             = 'Associate Member B'
    _typeC             = 'Associate Member C'
    _spore             = 'SPOREs'
    _non               = 'Non-EDRN Site'
    template           = 'eke.knowledge/site-index.html'
    subpage_types      = [Site, OrganizationalGroup]

    def get_context(self, request: HttpRequest, *args, **kwargs) -> dict:
        context = super().get_context(request, *args, **kwargs)

        for og in OrganizationalGroup.objects.child_of(self).order_by('title'):
            context[og.title.lower()] = og.group_members.all()

        context['ics']   = Site.objects.child_of(self).live().public().filter(memberType=self._ic)
        context['ncis']  = Site.objects.child_of(self).live().public().filter(memberType=self._nci)
        context['typeA'] = Site.objects.child_of(self).live().public().filter(memberType=self._typeA)
        context['typeB'] = Site.objects.child_of(self).live().public().filter(memberType=self._typeB)
        context['typeC'] = Site.objects.child_of(self).live().public().filter(memberType=self._typeC)
        context['spore'] = Site.objects.child_of(self).live().public().filter(memberType=self._spore)
        context['non']   = Site.objects.child_of(self).live().public().filter(memberType=self._non)

        sites = Site.objects.child_of(self).live().public().specific().order_by(Lower('title'))
        map_data = sites.values('title', 'pi__title', 'pi__city', 'pi__lat', 'pi__lon').exclude(pi__lat__isnull=True)
        site_names, pi_names, cities, lats, lons = [], [], [], [], []
        for item in map_data:
            site_names.append(item['title'])
            pi_names.append(item['pi__title'])
            cities.append(item['pi__city'])
            lats.append(item['pi__lat'])
            lons.append(item['pi__lon'])

        df = pandas.DataFrame({
            'Site': site_names,
            'PI': pi_names,
            'City': cities,
            'lat': lats,
            'lon': lons,
        })
        figure = scatter_mapbox(
            df, lat='lat', lon='lon', hover_name='Site', hover_data=['PI', 'City'],
            color_discrete_sequence=['fuchsia'], zoom=3, height=300
        )
        figure.update_layout(mapbox_style='open-street-map')
        figure.update_layout(margin={'r': 0, 't': 0, 'l': 0, 'b': 0})
        app = DjangoDash('SitesChart')
        app.layout = html.Div(className='row', children=[
            dcc.Graph(id='map-of-edrn-sites', figure=figure)
        ])
        return context

    class Meta:
        pass
    class RDFMeta:
        ingestor = Ingestor
        types = {
            _siteType: Site,
        }


class OrgGroupMember(Orderable):
    site = models.ForeignKey(
        Site, null=True, blank=True, verbose_name='Site', related_name='+', on_delete=models.CASCADE
    )
    pi = models.ForeignKey(
        Person, null=True, blank=True, verbose_name='Principal Investigator', related_name='+',
        on_delete=models.CASCADE
    )
    organ_name = models.CharField(max_length=120, blank=True, null=False, help_text='Organ(s)')
    group_num = models.IntegerField(null=False, default=0, help_text='Group Number')
    sort_order = models.IntegerField(null=False, default=0, help_text='Sort Order')
    member_type = models.CharField(max_length=30, blank=True, null=False, help_text='Member type(s)')
    role = models.CharField(max_length=30, blank=True, null=False, help_text='Role played')
    panels = [
        FieldPanel('site'),
        FieldPanel('pi'),
        FieldPanel('organ_name'),
        FieldPanel('group_num'),
        FieldPanel('sort_order'),
        FieldPanel('member_type'),
        FieldPanel('role')
    ]
    page = ParentalKey(OrganizationalGroup, on_delete=models.CASCADE, related_name='group_members')
    def __str__(self):
        return f'{self.organ_name}'
    class Meta:
        ordering = ['organ_name', 'group_num', 'sort_order', 'pi__title']


def _create_org_group_member(predicates: dict) -> OrgGroupMember:
    pi_uri = get_predicate_value(rdflib.term.URIRef('urn:edrn:predicates:person'), predicates)
    site_uri = get_predicate_value(rdflib.term.URIRef('urn:edrn:predicates:site'), predicates)
    role = get_predicate_value(rdflib.term.URIRef('urn:edrn:predicates:role'), predicates)
    sort_order = get_predicate_value(rdflib.term.URIRef('urn:edrn:predicates:sort_order'), predicates)
    group_num = get_predicate_value(rdflib.term.URIRef('urn:edrn:predicates:group_number'), predicates)
    mem_type = get_predicate_value(rdflib.term.URIRef('urn:edrn:predicates:member_type'), predicates)
    organ = get_predicate_value(rdflib.term.URIRef('urn:edrn:predicates:organ_name'), predicates)
    sort_order = int(sort_order) if len(sort_order) > 0 else 0
    group_num = int(group_num) if len(group_num) > 0 else 0
    pi = Person.objects.filter(identifier=pi_uri).first()
    if not pi:
        _logger.error('Member groups RDF references unknown person URI %s', pi_uri)
        return None
    site = Site.objects.filter(identifier=site_uri).first()
    if not site:
        _logger.error('Member groups RDF references unknown site URI %s', site_uri)
        return None
    return OrgGroupMember(
        site=site, pi=pi, organ_name=organ, group_num=group_num, sort_order=sort_order, member_type=mem_type,
        role=role
    )
