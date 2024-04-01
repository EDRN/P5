# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: protocols.'''

from .constants import MAX_SLUG_LENGTH
from .diseases import Disease
from .knowledge import KnowledgeObject, KnowledgeFolder
from .publications import Publication
from .rdf import RDFAttribute, RelativeRDFAttribute
from .sites import Site
from .utils import edrn_schema_uri as esu
from .utils import Ingestor as BaseIngestor, ghetto_plotly_legend, filter_by_user
from dash_dangerously_set_inner_html import DangerouslySetInnerHTML
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.fields import Field
from django.db.models.functions import Lower
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.text import slugify
from django_plotly_dash import DjangoDash
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from urllib.parse import urlparse
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.models import Orderable
from wagtail.search import index
import dash_core_components as dcc
import dash_html_components as html
import logging, rdflib, pandas, collections, plotly.express


_logger              = logging.getLogger(__name__)
_siteSpecificTypeURI = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/types.rdf#ProtocolSiteSpecific')
_protocolURIPrefix   = 'http://edrn.nci.nih.gov/data/protocols/'
_siteURIPrefix       = 'http://edrn.nci.nih.gov/data/sites/'
_protocolType        = 'http://edrn.nci.nih.gov/rdf/types.rdf#Protocol'
_internalIDPredicate = 'urn:internal:id'


class _ProjectFlagRDFAttribute(RDFAttribute):
    def compute_new_value(self, modelField: Field, value: str, predicates: dict) -> object:
        return super().compute_new_value(modelField, value == 'Project', predicates)


class _ComplexDescriptionRDFAttribute(RDFAttribute):
    def compute_new_value(self, modelField: Field, value: str, predicates: dict) -> object:
        for pred in (
            rdflib.DCTERMS.description,
            rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#objective'),
            rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#aims'),
            rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#outcome'),
            rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#secureOutcome')
        ):
            text = predicates.get(pred, [''])[0]
            if text:
                return super().compute_new_value(modelField, text, predicates)


class _CollaborativeGroupRDFAttribute(RDFAttribute):
    _aliases = {
        'Breast and Gynecologic Cancers Research': 'Breast and Gynecologic Cancers Research Group',
    }
    def compute_new_value(self, modelField: Field, value: str, predicates: dict) -> object:
        return super().compute_new_value(modelField, self._aliases.get(value.strip(), value.strip()), predicates)


class _PublicationSubjectURIRDFAttribute(RelativeRDFAttribute):
    def modify_field(self, obj: object, values: list, modelField: Field, predicates: dict) -> bool:
        results = Publication.objects.filter(subject_uris__identifier__in=values).values_list('identifier', flat=True)
        return super().modify_field(obj, [str(i) for i in results], modelField, predicates)


class Protocol(KnowledgeObject):
    template = 'eke.knowledge/protocol.html'
    parent_page_types = ['ekeknowledge.ProtocolIndex']
    page_description = 'Procedure for carrying out scientific research'
    coordinatingInvestigatorSite = models.ForeignKey(
        Site, null=True, blank=True, verbose_name='Coordinating Investigator Site',
        related_name='coordinated_protocols', on_delete=models.SET_NULL
    )
    leadInvestigatorSite = models.ForeignKey(
        Site, null=True, blank=True, verbose_name='Lead Investigator Site',
        related_name='leading_protocols', on_delete=models.SET_NULL
    )
    piName = models.CharField(blank=True, null=False, max_length=200, help_text='De-normalized PI name from lead site')
    involvedInvestigatorSites = ParentalManyToManyField(
        Site, blank=True, verbose_name='Involved Investigator Sites', related_name='involving_protocols'
    )
    publications = ParentalManyToManyField(
        Publication, blank=True, verbose_name='Publications', related_name='protocols'
    )
    cancer_types = ParentalManyToManyField(
        Disease, blank=True, verbose_name='Cancers Studied', related_name='protocols_analyzing'
    )
    isProject = models.BooleanField(
        null=False, blank=False, default=False,
        help_text='True if this is a project, not a protcol'
    )
    protocolID = models.IntegerField(
        null=True, blank=True, help_text='Number assigned by the DMCC but could be blank for non-EDRN protocols'
    )
    abbreviation = models.CharField(
        max_length=120, null=False, blank=True, help_text='Short and more convenient name for the protocol'
    )
    phasedStatus = models.PositiveIntegerField(blank=True, null=True, help_text='Not sure what this is')
    aims = models.TextField(null=False, blank=True, help_text='The long term goals of this protocol')
    analyticMethod = models.TextField(null=False, blank=True, help_text='How things in this protocol are analyzed')
    comments = models.TextField(null=False, blank=True, help_text='Your feedback on this protocol is appreciated!')
    start_date = models.TextField(null=False, blank=True, help_text='When this protocol began')
    estimated_finish_date = models.TextField(null=False, blank=True, help_text='A guess as to when this protocol will end')
    finish_date = models.TextField(null=False, blank=True, help_text='When this protocol ceased')
    # 🤬 Get bent    # collaborativeGroupsDeNormalized = models.CharField(max_length=400, blank=True, null=False, help_text='🙄')
    collaborativeGroup = models.CharField(max_length=400, blank=True, null=False, help_text='Collaborative Group')
    kind = models.CharField(max_length=80, blank=True, null=False, help_text='Protocol type')
    outcome = models.TextField(null=False, blank=True, help_text="What this protocol's net result was")
    secure_outcome = models.TextField(null=False, blank=True, help_text="What this protocol's secret net result was")
    content_panels = KnowledgeObject.content_panels + [
        InlinePanel('fields_of_research', label='Fields of Research'),  # 351
        FieldPanel('coordinatingInvestigatorSite'),
        FieldPanel('leadInvestigatorSite'),
        FieldPanel('involvedInvestigatorSites'),
        FieldPanel('cancer_types'),
        FieldPanel('isProject'),
        FieldPanel('protocolID'),
        FieldPanel('abbreviation'),
        FieldPanel('phasedStatus'),
        FieldPanel('aims'),
        FieldPanel('analyticMethod'),
        FieldPanel('comments'),
        FieldPanel('start_date'),
        FieldPanel('estimated_finish_date'),
        FieldPanel('finish_date'),
        FieldPanel('collaborativeGroup'),
        FieldPanel('kind'),
        FieldPanel('publications'),
        FieldPanel('outcome'),
        FieldPanel('secure_outcome')
    ]
    search_fields = KnowledgeObject.search_fields + [
        index.SearchField('abbreviation'),
        index.SearchField('protocolID'),
        index.FilterField('piName'),
        index.FilterField('collaborativeGroup'),
        index.FilterField('cancer_types'),
        index.FilterField('outcome'),
        index.FilterField('secure_outcome'),
    ]
    class Meta:
        pass
    class RDFMeta:
        fields = {
            esu('coordinatingInvestigatorSite'): RelativeRDFAttribute('coordinatingInvestigatorSite', scalar=True),
            esu('leadInvestigatorSite'): RelativeRDFAttribute('leadInvestigatorSite', scalar=True),
            esu('involvedInvestigatorSites'): RelativeRDFAttribute('involvedInvestigatorSites', scalar=False),
            esu('cancerType'): RelativeRDFAttribute('cancer_types', scalar=False),
            esu('projectFlag'): _ProjectFlagRDFAttribute('isProject', scalar=True),
            esu('abbreviatedName'): RDFAttribute('abbreviation', scalar=True),
            esu('fieldOfResearch'): RDFAttribute('fields_of_research', scalar=False),  # #351
            esu('collaborativeGroupText'): _CollaborativeGroupRDFAttribute('collaborativeGroup', scalar=True),
            esu('phasedStatus'): RDFAttribute('phasedStatus', scalar=True),
            esu('aims'): RDFAttribute('aims', scalar=True),
            esu('analyticMethod'): RDFAttribute('analyticMethod', scalar=True),
            esu('comments'): RDFAttribute('comments', scalar=True),
            esu('startDate'): RDFAttribute('start_date', scalar=True),
            esu('estimatedFinishDate'): RDFAttribute('estimated_finish_date', scalar=True),
            esu('finishDate'): RDFAttribute('finish_date', scalar=True),
            esu('publication'): _PublicationSubjectURIRDFAttribute('publications', scalar=False),
            _internalIDPredicate: RDFAttribute('protocolID', scalar=True),
            str(rdflib.DCTERMS.title): RDFAttribute('title', scalar=True),
            str(rdflib.DCTERMS.description): _ComplexDescriptionRDFAttribute('description', scalar=True),
            esu('outcome'): _ComplexDescriptionRDFAttribute('outcome', scalar=True),
            esu('secureOutcome'): _ComplexDescriptionRDFAttribute('secure_outcome', scalar=True),
            esu('protocolType'): RDFAttribute('kind', scalar=True)
        }

    def _authentication(self, request: HttpRequest) -> dict:
        '''Given a request, determine if the user is authenticated and what the login link would be if not.'''
        params = {'authenticated': request.user.is_authenticated}
        if not params['authenticated']:
            params['login'] = reverse('wagtailcore_login') + '?next=' + request.path
        return params

    def get_context(self, request: HttpRequest, *args, **kwargs) -> dict:
        '''Get the context for the page template.'''
        context = super().get_context(request, args, kwargs)
        from .models import RDFIngest
        limit = RDFIngest.for_request(request).edrn_protocol_limit
        context['nonEDRNProtocol'] = self.protocolID >= limit
        from .sciencedata import DataCollection
        dcs = DataCollection.objects.filter(generating_protocol=self).live().order_by(Lower('title'))
        total_collections = dcs.count()
        dcs = filter_by_user(dcs, request.user)
        invisible_collections = total_collections - dcs.count()
        if invisible_collections:
            context.update(self._authentication(request))
        context['data_collections'] = dcs
        context['invisible_collections'] = invisible_collections
        from eke.biomarkers.biomarker import Biomarker
        bms = Biomarker.objects.filter(protocols=self).live().order_by(Lower('title'))
        context['biomarkers'] = bms
        context['cancer_types'] = [i for i in self.cancer_types.all().order_by('title').values_list('title', flat=True)]
        context['publications'] = [i for i in self.publications.order_by(Lower('title'))]

        # Show the new secure outcome only for logged in users
        # context['show_secure_outcome'] = request and request.user.is_authenticated
        #
        # Actually …
        #
        # In https://github.com/EDRN/P5/issues/348#issuecomment-1998265624 @hoodriverheather requests
        # that we don't show the secure outcome
        context['show_secure_outcome'] = False

        # Fields of research ("f_o_rs") is multi-valued now #351
        context['f_o_rs'] = [i for i in self.fields_of_research.all().order_by('value')]

        return context

    def data_table(self) -> dict:
        if self.leadInvestigatorSite:
            if self.leadInvestigatorSite.pi:
                pi_url = self.leadInvestigatorSite.pi.url
                pi_name = self.leadInvestigatorSite.pi.title
            else:
                pi_url = self.leadInvestigatorSite.url
                pi_name = self.leadInvestigatorSite.title
        else:
            pi_url = pi_name = None

        cgs = []
        for cg in self.collaborativeGroup.split(', '):
            cg = cg.split(' ')[0] if cg else 'UNKNOWN'
            if cg == 'Breast': cg = 'Breast/Gyn'
            cgs.append(cg)

        # #351 — f_o_rs = "fields of research", which I guess technically should be "fs_o_r" 😅
        f_o_rs = ', '.join([i for i in self.fields_of_research.all().values_list('value', flat=True).order_by('value')])

        return {
            'pi_name': pi_name,
            'pi_url': pi_url,
            'f_o_rs': f_o_rs,
            # Turned off for #190
            # 'diseases': ', '.join([str(i) for i in self.cancer_types.values_list('title', flat=True).order_by('title')]),
            'cg': ', '.join(cgs),
            **super().data_table()
        }


class ProtocolFieldOfResearch(Orderable):
    '''Multi-valued support for RDF "fieldOfResearch" field.

    Supports #351.
    '''
    value = models.CharField(
        max_length=25, blank=False, null=False, default='Field of research', help_text='Field of research'
    )
    page = ParentalKey(Protocol, on_delete=models.CASCADE, related_name='fields_of_research')
    panels = [FieldPanel('value')]
    def __str__(self): return self.value  # noqa: E704


class Ingestor(BaseIngestor):
    def _dmcc_code(self, uri: rdflib.URIRef) -> str:
        '''For the given subject URI return what would be the DMCC protocol ID.'''
        return urlparse(uri).path.split('/')[-1]

    def getSlug(self, uri: rdflib.URIRef, predicates: dict) -> str:
        '''For protocols we want to include the protocol ID as part of the URL.'''
        protocol_id = self._dmcc_code(uri)
        title = predicates.get(rdflib.DCTERMS.title, ['«unknown protocol»'])[0]
        return slugify(f'{protocol_id} {title}')[:MAX_SLUG_LENGTH]

    def readRDF(self) -> dict:
        '''Read the RDF.

        In this subclass implementation, we "inject" an extra statement so we can set the computed
        site ID.
        '''
        self.statements = super().readRDF()
        for subj, preds in self.statements.items():
            typeURI = str(preds[rdflib.RDF.type][0])
            if typeURI != _protocolType: continue
            dmccCode = self._dmcc_code(subj)
            preds[rdflib.URIRef(_internalIDPredicate)] = [dmccCode]
        return self.statements

    def setInvolvedInvestigatorSites(self):
        protocolToSites = {}
        for uri, predicates in self.filter_by_rdf_type(self.statements, _siteSpecificTypeURI):
            protNum, siteNum = urlparse(uri).path.split('/')[-1].split('-')
            protID, siteID = _protocolURIPrefix + protNum, _siteURIPrefix + siteNum
            protocol = Protocol.objects.filter(identifier=protID).first()
            if protocol:
                sites = protocolToSites.get(protocol, set())
                sites.add(siteID)
                protocolToSites[protocol] = sites
        for protocol, siteIDs in protocolToSites.items():
            sites = Site.objects.filter(identifier__in=siteIDs)
            protocol.involvedInvestigatorSites.set(sites, clear=True)
            try:
                protocol.save()
            except ValidationError:
                _logger.exception('Cannot save protocol %s after adding involved investigators', protocol.identifier)

    def promote_search_results(self):
        '''Make search descriptions for the newly-created ``protocols``.'''
        for protocol in Protocol.objects.child_of(self.folder):
            if protocol.kind == 'Validation':
                kind = 'Validation study'
            elif protocol.kind == 'Single':
                kind = 'Single protocol'
            elif protocol.kind == 'Other specify' or not protocol.kind:
                kind = 'protocol, project, or study'
            else:
                kind = protocol.kind
            first_letter = kind[0].lower()
            article = 'an' if first_letter in ('a', 'e', 'i', 'o', 'u') else 'a'
            promotion = f'"{protocol.title}" is {article} {kind} of the Early Detection Research Network.'
            protocol.search_description = promotion
            try:
                protocol.save()
            except ValidationError:
                _logger.exception('Cannot save protocol %s after adding search description', protocol.identifier)

    def ingest(self):
        n, u, d = super().ingest()
        self.setInvolvedInvestigatorSites()
        self.promote_search_results()
        return n, u, d


class ProtocolIndex(KnowledgeFolder):
    template = 'eke.knowledge/protocol-index.html'
    subpage_types = [Protocol]
    page_description = 'Container for protocols'

    def get_contents(self, request: HttpRequest) -> object:
        matches = Protocol.objects.child_of(self).live().public().order_by(Lower('title'))

        pi, fields, cg = request.GET.get('piName'), request.GET.getlist('fieldOfResearch'), request.GET.get('collab_group')
        filter = {}
        if pi: filter['piName__exact'] = pi
        if fields: filter['fields_of_research__value__in'] = fields
        if cg: filter['collaborativeGroup'] = cg  # cannot use __contains or __icontains because ``search`` below balks
        q = Q(**filter)
        # According to https://docs.wagtail.org/en/stable/topics/search/indexing.html:
        #     It’s not possible to filter on any index.FilterFields within index.RelatedFields using the
        #     QuerySet API … Filtering on index.RelatedFields with the QuerySet API is planned for a future
        #     release of Wagtail.
        # So this means we can't do:
        #     if cgs: filter['collaborativeGroups__value__in'] = cgs
        # because when we then do the search on that filtered set, we get
        #      wagtail.search.backends.base.FilterFieldError: Cannot filter search results with field "value".
        #      Please add index.FilterField('value') to Protocol.search_fields
        # So we search instead on our de-normalized textual concatenation of the collaborative groups that
        # are kept up-to-date via the Django signal mechanism and do this instead:
        # if cgs:
        #     cgQueries = [Q(collaborativeGroupsDeNormalized__icontains=cg) for cg in cgs]
        #     q = q & functools.reduce(operator.or_, cgQueries)
        # ↑ NOPE, this doesn't work because we can't get a Django signal on a pre_save when a CG is
        # added/deleted so just give the @*#$@ up on this 🤬

        matches = matches.filter(q)
        query = request.GET.get('query')
        if query: matches = matches.search(query)

        return matches

    def faceted_markup(self, request):
        pages, rows = self.get_contents(request), []
        for page in pages:
            rows.append(render_to_string('eke.knowledge/protocol-row.html', {'protocol': page.specific}))
        return ''.join(rows)

    def get_context(self, request: HttpRequest, *args, **kwargs) -> dict:
        context = super().get_context(request, *args, **kwargs)
        matches = context['knowledge_objects']

        # 🔮 Get this from settings?
        palette = plotly.express.colors.qualitative.Dark24

        # When from a search, the `facet` is conveniently available on the `matches` which is not a
        # `PageQuerySet` but a `SearchResults`. However, it's problematic since it doesn't support all
        # the ordering (order_by, Lower), so I'm going to use `values_list` instead.
        #
        # Also, now that we use DataTables, we don't use SearchResults at all!
        #
        # try:
        #     field_facets = matches.facet('fieldOfResearch')
        #     fields_frame = pandas.DataFrame(field_facets.items(), columns=('Field', 'Count'))

        #     group_facets = matches.facet('collaborativeGroup')
        #     groups_frame = pandas.DataFrame(group_facets.items(), columns=('Group', 'Count'))

        #     diseases_facets = matches.facet('cancer_types')
        #     mapped_to_disease_names = []
        #     while len(diseases_facets) > 0:
        #         disease_pk, count = diseases_facets.popitem(last=False)
        #         disease = Disease.objects.filter(pk=disease_pk).first()
        #         if disease:
        #             mapped_to_disease_names.append((disease.title, count))
        #     diseases_facets = collections.OrderedDict(mapped_to_disease_names)
        #     diseases_frame = pandas.DataFrame(diseases_facets.items(), columns=('Disease', 'Count'))
        # except AttributeError:

        c = collections.Counter(matches.values_list('fields_of_research__value', flat=True))
        fields, amounts = [i[0] for i in c.items()], [i[1] for i in c.items()]
        fields_frame = pandas.DataFrame({'Field': fields, 'Count': amounts})
        fields_legend = ghetto_plotly_legend([i[0] for i in c.most_common()], palette)

        matches = matches.exclude(collaborativeGroup='').exclude(collaborativeGroup__contains=',')
        c = collections.Counter(matches.values_list('collaborativeGroup', flat=True))
        groups, amounts = [i[0] for i in c.items()], [i[1] for i in c.items()]
        groups_frame = pandas.DataFrame({'Group': groups, 'Count': amounts})
        groups_legend = ghetto_plotly_legend([i[0] for i in c.most_common()], palette)

        # #189: turn off for now
        # c = collections.Counter(matches.values_list('cancer_types', flat=True))
        # diseases = [Disease.objects.filter(pk=i[0]).first().title for i in c.most_common() if i[0] is not None]
        # amounts = [i[1] for i in c.items() if i[0] is not None]
        # diseases_frame = pandas.DataFrame({'Disease': diseases, 'Count': amounts})
        # diseases_legend = ghetto_plotly_legend(diseases, palette)

        fields_figure = plotly.express.pie(
            fields_frame, values='Count', names='Field', title='Fields of Research', color_discrete_sequence=palette,
            width=400
        )
        # Why did I do this? Turn it back on #190
        # fields_figure.update_traces(hoverinfo='skip', hovertemplate=None)
        fields_figure.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20))

        groups_figure = plotly.express.pie(
            groups_frame, values='Count', names='Group', title='Collaborative Groups', color_discrete_sequence=palette,
            width=400
        )
        # Why did I do this? Turn it back on #190
        # groups_figure.update_traces(hoverinfo='skip', hovertemplate=None)
        groups_figure.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20))

        # #189: turn off for now
        # diseases_figure = plotly.express.pie(
        #     diseases_frame, values='Count', names='Disease', title='Diseases Studied', color_discrete_sequence=palette,
        #     width=400
        # )
        # Why did I do this? Turn it back on #190
        # diseases_figure.update_traces(hoverinfo='skip', hovertemplate=None)
        # diseases_figure.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20))

        app = DjangoDash('ProtocolDashboard')  # ← referenced in protocol-index.html
        app.layout = html.Div(className='container', children=[
            html.Div(className='row', children=[
                html.Div(className='col-md-6', children=[  # changed ``col-md-4`` → ``col-md-6`` for #189
                    dcc.Graph(id='fields-of-research', figure=fields_figure),
                    DangerouslySetInnerHTML(fields_legend),
                ]),
                html.Div(className='col-md-6', children=[  # changed ``col-md-4`` → ``col-md-6`` for #189
                    dcc.Graph(id='collaborative-groups', figure=groups_figure),
                    DangerouslySetInnerHTML(groups_legend),
                ]),
                # #189 turn off for now
                # html.Div(className='col-md-4', children=[
                #     dcc.Graph(id='diseases', figure=diseases_figure),
                #     DangerouslySetInnerHTML(diseases_legend),
                # ]),
            ]),
        ])
        return context

    def serve(self, request: HttpRequest) -> HttpResponse:
        '''Overridden service.

        We override serve in order to handle the ``ajax=fields-of-research`` request. Supports #351.
        '''
        if request.GET.get('ajax') == 'fields-of-research':
            f_o_rs = ProtocolFieldOfResearch.objects.distinct().values_list('value', flat=True).order_by('value')
            return JsonResponse({'data': [i for i in f_o_rs]})
        else:
            return super().serve(request)

    class Meta:
        pass
    class RDFMeta:
        ingestor = Ingestor
        types = {
            _protocolType: Protocol,
        }
