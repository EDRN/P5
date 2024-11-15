# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: science data.'''


from .bodysystems import BodySystem
from .knowledge import KnowledgeObject, KnowledgeFolder
from .protocols import Protocol
from .rdf import RelativeRDFAttribute, RDFAttribute
from .utils import Ingestor as BaseIngestor, filter_by_user, ghetto_plotly_legend
from dash_dangerously_set_inner_html import DangerouslySetInnerHTML
from django.contrib.auth.models import Group
from django.db import models
from django.db.models import Q
from django.db.models.fields import Field
from django.db.models.functions import Lower
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django_plotly_dash import DjangoDash
from modelcluster.fields import ParentalManyToManyField, ParentalKey
from urllib.parse import urlparse
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, PageViewRestriction
from wagtail.search import index
import dash_core_components as dcc
import dash_html_components as html
import logging, rdflib, plotly.express, collections, pandas

_logger = logging.getLogger(__name__)

_dataStatisticTypeURI = 'urn:edrn:types:labcas:statistics'


def _pre(frag: str) -> str:
    '''Make a predicate in the EDRN namespace ``urn:edrn:predicates:`` for the given ``frag``ment.'''
    return 'urn:edrn:predicates:' + frag


class _PIRDFAttribute(RDFAttribute):
    def compute_new_value(self, modelField: Field, value: str, predicates: dict) -> object:
        protocolURI = predicates.get(rdflib.URIRef(_pre('protocol')), [])
        if protocolURI:
            results = Protocol.objects.filter(identifier__exact=protocolURI[0])
            if results.count() > 0:
                return super().compute_new_value(modelField, results.first().piName, predicates)
        return super().compute_new_value(modelField, value, predicates)


class _BodySystemRDFAttribute(RelativeRDFAttribute):
    def modify_field(self, obj: object, values: list, modelField: Field, predicates: dict) -> bool:
        results = BodySystem.objects.filter(title__in=[str(i) for i in values]).values_list('identifier', flat=True)
        return super().modify_field(obj, [rdflib.URIRef(i) for i in results], modelField, predicates)


class DataStatistic(KnowledgeObject):
    '''A statsitic about data in LabCAS.

    The subject URI ``identifier`` points to a LabCAS Solr endpoint, and the cardinality is the count of
    items at that endpoint.
    '''
    parent_page_types = ['ekeknowledge.DataCollectionIndex']
    cardinality = models.PositiveIntegerField(blank=False, null=False, default=0, help_text='Count of items')
    content_panels = KnowledgeObject.content_panels + [FieldPanel('cardinality')]
    class RDFMeta:
        fields = {
            _pre('cardinality'): RDFAttribute('cardinality', scalar=True)
        }


class DataCollection(KnowledgeObject):
    '''Corresponds to a single collection of data in LabCAS.'''
    template = 'eke.knowledge/data-collection.html'
    page_description = 'Collection of data from the Data Commons (LabCAS)'
    parent_page_types = ['ekeknowledge.DataCollectionIndex']
    preview_modes = []
    generating_protocol = models.ForeignKey(
        Protocol, null=True, blank=True, verbose_name='Protocol that produced this data',
        related_name='generated_data_collections', on_delete=models.SET_NULL
    )
    investigator_name = models.CharField(max_length=80, blank=True, null=False, help_text='Name of PI')
    collaborative_group = models.CharField(max_length=80, blank=True, null=False, help_text='Collaborative group')
    associated_organs = ParentalManyToManyField(
        BodySystem, blank=True, verbose_name='Associated Organs', related_name='organs_in_data'
    )
    content_panels = KnowledgeObject.content_panels + [
        FieldPanel('generating_protocol'),
        FieldPanel('investigator_name'),
        FieldPanel('collaborative_group'),
        FieldPanel('associated_organs'),
        InlinePanel('owner_principals', label='Owner Principals'),
        InlinePanel('data_collection_disciplines', label='Disciplines'),
        InlinePanel('data_collection_categories', label='Data Categories'),
    ]
    search_fields = KnowledgeObject.search_fields + [
        index.RelatedFields('generating_protocol', [index.AutocompleteField('title')]),
        index.RelatedFields('associated_organs', [index.AutocompleteField('title')]),
        index.SearchField('investigator_name'),
    ]

    def get_context(self, request: HttpRequest, *args, **kwargs) -> dict:
        context = super().get_context(request, *args, **kwargs)

        # Add in all the juicy detail that we otherwise provide via data_table
        context.update(self.data_table())
        # but improve on organ handling
        context['organs'] = self.associated_organs.all().order_by('title')

        # Now find all biomarkers
        context['biomarkers'] = self.ekebiomarkers_biomarker_observed.all().order_by('title')
        # 🔮 Note: data collections can also be referenced by ekebiomarkers_biomarkerbodysystem_observed
        # and by ekebiomarkers_bodysystemstudy_observed. Note that none of these are filled in, though,
        # because in the Biomarker Database, you can only associated data collections with biomarkers,
        # despite the model allowing it.
        #
        # If the Biomarker Database is ever updated to the model and the edrn.bmdb RDF generation follows
        # suit, then we'll need to update this too.

        return context

    def data_table(self) -> dict:
        '''Return the JSON-compatible dictionary describing this science data collection.'''

        attributes = super().data_table()

        if self.generating_protocol:
            attributes['protocol'] = self.generating_protocol.title
            attributes['protocol_url'] = self.generating_protocol.url
            if self.generating_protocol.leadInvestigatorSite:
                if self.generating_protocol.leadInvestigatorSite.pi:
                    attributes['pi'] = self.generating_protocol.leadInvestigatorSite.pi.title
                    attributes['pi_url'] = self.generating_protocol.leadInvestigatorSite.pi.url
                else:
                    attributes['pi'] = self.generating_protocol.leadInvestigatorSite.title
                    attributes['pi_url'] = self.generating_protocol.leadInvestigatorSite.url
            else:
                attributes['pi'] = self.investigator_name if self.investigator_name else '(unknown)'
                attributes['pi_url'] = None
        else:
            attributes['protocol'] = '(unknown)'
            attributes['pi'] = self.investigator_name if self.investigator_name else '(unknown)'
            attributes['pi_url'] = None

        if self.associated_organs.count() > 0:
            attributes['organs'] = ', '.join([str(i) for i in self.associated_organs.all().order_by('title')])
        else:
            attributes['organs'] = '(unknown)'

        if self.collaborative_group:
            truncated_group_name = self.collaborative_group.split(' ')[0]
            if truncated_group_name == 'Breast':
                truncated_group_name = 'Breast/Gyn'
            attributes['cg'] = truncated_group_name
        else:
            attributes['cg'] = '(unknown)'

        return attributes

    class RDFMeta:
        fields = {
            _pre('protocol'): RelativeRDFAttribute('generating_protocol', scalar=True),
            _pre('pi'): _PIRDFAttribute('investigator_name', scalar=True),
            _pre('organ'): _BodySystemRDFAttribute('associated_organs', scalar=False),
            _pre('collaborativeGroup'): RDFAttribute('collaborative_group', scalar=True),
            _pre('ownerPrincipal'): RDFAttribute('owner_principals', scalar=False),
            _pre('discipline'): RDFAttribute('data_collection_disciplines', scalar=False),
            _pre('dataCategory'): RDFAttribute('data_collection_categories', scalar=False),
        }


class PrincipalOwner(Orderable):
    '''Principal owner of a data collection.'''
    value = models.CharField(max_length=512, blank=False, null=False, default='Owner', help_text='DN of principal')
    page = ParentalKey(DataCollection, on_delete=models.CASCADE, related_name='owner_principals')
    panels = [FieldPanel('value')]
    def __str__(self): return self.value  # noqa: E704


class Discipline(Orderable):
    '''Branch of knowledge curated within a data collection.'''
    value = models.CharField(
        max_length=256, blank=False, null=False, default='Discipline', help_text='Branch of knowledge or study'
    )
    page = ParentalKey(DataCollection, on_delete=models.CASCADE, related_name='data_collection_disciplines')
    panels = [FieldPanel('value')]


class DataCategory(Orderable):
    '''A general category of data, buh.'''
    value = models.CharField(max_length=256, blank=False, null=False, default='Data category', help_text='Category')
    page = ParentalKey(DataCollection, on_delete=models.CASCADE, related_name='data_collection_categories')
    panels = [FieldPanel('value')]


class Ingestor(BaseIngestor):
    '''Custom ingestor for scientific data collections.'''

    _public_group = 'All Users'

    def getTitle(self, uri: rdflib.URIRef, predicates: dict) -> str:
        typeURI = str(predicates[rdflib.RDF.type][0])
        if typeURI == _dataStatisticTypeURI:
            return urlparse(uri).path.split('/')[-1].capitalize()
        else:
            return super().getTitle(uri, predicates)

    def _de_dn(self, dn: str) -> str:
        '''De-"distinguished name"-ify the given ``dn``.'''
        return dn.split(',')[0].split('=')[1]

    def add_search_promotions(self, data_collections):
        for dc in data_collections:
            promotion = f'"{dc.title}" is scientific data collected by Early Detection Research Network.'
            dc.search_description = promotion
            dc.save()

    def ingest(self):
        '''Override ingest so we can set page view restrictions on certain data collections.'''
        n, u, d = super().ingest()
        ingested = n | u
        for collection in [i for i in ingested if isinstance(i, DataCollection)]:
            # First, clear up any PageViewRestrictions from last time
            PageViewRestriction.objects.filter(page=collection).delete()

            # Next get the groups
            groups = set([self._de_dn(i) for i in collection.owner_principals.values_list('value', flat=True)])
            if self._public_group not in groups:
                # The public group "All Users" isn't here, so we need to restrict it
                pvr = PageViewRestriction(page=collection, restriction_type='groups')
                pvr.save()
                pvr.groups.set(Group.objects.filter(name__in=groups), clear=True)
        self.add_search_promotions(n)
        return n, u, d


class DataCollectionIndex(KnowledgeFolder):
    template = 'eke.knowledge/data-collection-index.html'
    subpage_types = [DataCollection, DataStatistic]
    page_description = 'Container for data collections'

    preamble = RichTextField(blank=True, null=False, help_text='Text to appear at the top of the page')

    metadata_collection_form = models.ForeignKey(
        'edrnsitecontent.MetadataCollectionFormPage', null=True, blank=True,
        verbose_name='Metadata Collection Form', related_name='+',
        help_text='Which page to use as the metadata collection form',
        on_delete=models.SET_NULL
    )
    content_panels = KnowledgeFolder.content_panels + [
        FieldPanel('preamble'),
        FieldPanel('metadata_collection_form')
    ]

    def get_vocabulary(self, name) -> list:
        '''Get a "vocabulary" of known values for the field ``name`` for our contained subpage.'''
        if name == 'organ':
            return DataCollection.objects.child_of(self).live().public().values_list(
                'associated_organs__title', flat=True
            ).distinct().exclude(associated_organs__title__isnull=True).order_by('associated_organs__title')
        else:
            return super().get_vocabulary(name)

    def get_contents(self, request: HttpRequest):
        matches = filter_by_user(DataCollection.objects.child_of(self).live().order_by(Lower('title')), request.user)
        organs = request.GET.getlist('organ')  # other facets?
        filter = {}
        if organs: filter['associated_organs__title__in'] = organs
        matches = matches.filter(Q(**filter))
        query = request.GET.get('query')
        if query: matches = matches.search(query)
        return matches

    def faceted_markup(self, request):
        pages, rows = self.get_contents(request), []
        for page in pages:
            rows.append(render_to_string('eke.knowledge/data-collection-row.html', {'data_collection': page.specific}))
        return ''.join(rows)

    def get_context(self, request: HttpRequest, *args, **kwargs) -> dict:
        app = DjangoDash('ScienceDataDashboard')  # ← referenced in data-collection-index.html

        context = super().get_context(request, *args, **kwargs)
        context['statistics'] = DataStatistic.objects.child_of(self).order_by('title')
        matches = context['knowledge_objects']

        # 🔮 Get this from settings?
        palette = plotly.express.colors.qualitative.Dark24

        c = collections.Counter(Discipline.objects.filter(page__in=matches).values_list('value', flat=True))
        discs, amounts = [i[0] for i in c.items() if i[0] is not None], [i[1] for i in c.items() if i[0] is not None]
        discs_frame = pandas.DataFrame({'Discipline': discs, 'Count': amounts})
        discs_figure = plotly.express.pie(
            discs_frame, values='Count', names='Discipline', title='Disciplines',
            color_discrete_sequence=palette
        )
        discs_figure.update_traces(hoverinfo='skip', hovertemplate=None)
        discs_figure.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
        discs_legend = ghetto_plotly_legend([i[0] for i in c.most_common()], palette)

        c = collections.Counter(BodySystem.objects.filter(organs_in_data__in=matches).values_list('title', flat=True))
        organs, amounts = [i[0] for i in c.items() if i[0] is not None], [i[1] for i in c.items() if i[0] is not None]
        organs_frame = pandas.DataFrame({'Organ': organs, 'Count': amounts})
        organs_figure = plotly.express.pie(
            organs_frame, values='Count', names='Organ', title='Organs',
            color_discrete_sequence=palette
        )
        organs_figure.update_traces(hoverinfo='skip', hovertemplate=None)
        organs_figure.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
        organs_legend = ghetto_plotly_legend([i[0] for i in c.most_common()], palette)

        c = collections.Counter(DataCategory.objects.filter(page__in=matches).values_list('value', flat=True))
        cats, amounts = [i[0] for i in c.items() if i[0] is not None], [i[1] for i in c.items() if i[0] is not None]
        cats_frame = pandas.DataFrame({'Category': cats, 'Count': amounts})
        cats_figure = plotly.express.pie(
            cats_frame, values='Count', names='Category', title='Data Categories',
            color_discrete_sequence=palette
        )
        cats_figure.update_traces(hoverinfo='skip', hovertemplate=None)
        cats_figure.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
        cats_legend = ghetto_plotly_legend([i[0] for i in c.most_common()], palette)

        app.layout = html.Div(className='container', children=[
            html.Div(className='row', children=[
                html.Div(className='col-md-4', children=[
                    dcc.Graph(id='disciplines', figure=discs_figure),
                    DangerouslySetInnerHTML(discs_legend),
                ]),
                html.Div(className='col-md-4', children=[
                    dcc.Graph(id='organs', figure=organs_figure),
                    DangerouslySetInnerHTML(organs_legend),
                ]),
                html.Div(className='col-md-4', children=[
                    dcc.Graph(id='categories', figure=cats_figure),
                    DangerouslySetInnerHTML(cats_legend),
                ]),
            ]),
        ])

        return context

    class RDFMeta:
        ingestor = Ingestor
        types = {
            'urn:edrn:types:labcas:collection': DataCollection,
            _dataStatisticTypeURI: DataStatistic,
        }
