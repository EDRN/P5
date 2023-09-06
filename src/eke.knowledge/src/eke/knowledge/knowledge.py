# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: classes to represent the base level of knowledge.'''

from .constants import MAX_URI_LENGTH
from .rdf import RDFAttribute
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.http import HttpRequest
from django.http import HttpResponse, JsonResponse
from django.http.request import QueryDict
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.models import Page, Orderable
from wagtail.search import index
from wagtailmetadata.models import MetadataPageMixin
import rdflib, dataclasses, re, logging

_order_regex = re.compile(r'^order\[([0-9]+)]\[(dir|column)]$')
_col_regex = re.compile(r'^columns\[([0-9)+])]\[(data|name|search|searchable|orderable)](\[(value|regex)])?$')
_logger = logging.getLogger(__name__)


def _request_parameters(qd: QueryDict):
    while True:
        try:
            key, values = qd.popitem()
            yield key, values
        except KeyError:
            break


class KnowledgeObject(MetadataPageMixin, Page):
    '''An object in a knowledge environment that has an RDF subject URI.'''
    template = 'eke.knowledge/knowledge-object.html'
    search_auto_update = True
    page_description = 'An object described by RDF'

    # I'd like this to be the primary_key for the table but Wagtail expects integers 🤷‍♀️
    identifier = models.CharField(
        'subject URI',
        blank=False, null=False, primary_key=False, unique=True, max_length=MAX_URI_LENGTH,
        help_text='RDF subject URI that uniquely identifies this object',
    )
    description = models.TextField(blank=True, null=False, help_text='A summary or descriptive abstract')

    content_panels = Page.content_panels + [FieldPanel('identifier'), FieldPanel('description')]
    search_fields = Page.search_fields + [
        index.SearchField('identifier'),
        index.SearchField('description')
    ]

    def data_table(self) -> dict:
        return {'identifier': self.identifier, 'title': self.title, 'url': self.url, 'description': self.description}

    class Meta:
        pass
    class RDFMeta:
        '''Resource Description Format metadata.

        The ``fields`` are a mapping from RDF predicate URI to a ``RDFAttribute`` instance. For knowledge
        object, we don't need theDublin Core title (titles are treated specially since they're required at
        instantiation time (for slugs, SEO, etc.) and may have more complex generation needs;
        see ``.utils.Ingestor``.
        '''
        fields = {
            # Although the title gets special treatment in ingest, we also declare it here so that if the
            # title of an object changes we can make the appropriate updates:
            str(rdflib.DCTERMS.title): RDFAttribute('title', scalar=True),
            str(rdflib.DCTERMS.description): RDFAttribute('description', scalar=True)
        }


@dataclasses.dataclass(init=False, order=True, frozen=False)
class DataTableReference(object):
    '''An abstract DataTables column or ordering reference.'''
    priority: int
    def __init__(self, priority: int):
        self.priority = priority
    def __hash__(self):
        return hash(self.priority)


class DataTableColumn(DataTableReference):
    '''A searchable, sortable column in a data table.'''
    data: str
    name: str
    searchable: bool
    orderable: bool
    search_value: str
    search_regex: bool
    def __repr__(self):
        return f'{self.__class__.__name__}(data={self.data},searchable={self.searchable})'


class DataTableOrdering(DataTableReference):
    '''A sort request for a column in the table.'''
    column: int
    ascending: bool
    def __repr__(self):
        return f'{self.__class__.__name__}(priority={self.priority},column={self.column},ascending={self.ascending})'


class KnowledgeFolder(MetadataPageMixin, Page):
    '''A container for Knowledge Objects.'''

    ingest         = models.BooleanField(default=True, help_text='Enable or disable ingest for this folder')
    ingest_order   = models.IntegerField(blank=False, null=False, default=0, help_text='Relative ordering of ingest')
    subpage_types  = [KnowledgeObject]
    template       = 'eke.knowledge/knowledge-folder.html'

    page_description = 'Container for knowledge objects'

    content_panels = Page.content_panels + [
        FieldPanel('ingest'),
        FieldPanel('ingest_order'),
        InlinePanel('rdf_sources', label='RDF Sources'),
    ]

    search_auto_update = False

    def get_vocabulary(self, name: str) -> list:
        '''Get a "vocabulary" of known values for the field ``name`` for our contained subpage.

        In the event we have multiple subpage types, we use only the first one. We look at immediate child
        pages only and those that are live, and return the vocabulary in lexicographic order.
        '''
        cls, excl = self.subpage_types[0], Q(**{f'{name}__exact': ''})  # Get rid of empties
        return cls.objects.child_of(self).live().exclude(excl).values_list(name, flat=True).distinct().order_by(Lower(name))

        # 🔮 Possible way to include counts on facets:
        # facets = cls.objects.child_of(self).live().exclude(excl).search(MatchAll()).facet(name)
        # return [{'label': i[0], 'count': i[1]} for i in facets.items()]

    def faceted_markup(self, request: HttpRequest) -> str:
        '''Yield marked up HTML for a faceted ajax ``request``.

        If subclassed folder-type pages want faceted navigation, they must implement this method, typically
        by using ``render_to_string`` repeatedly over matching subpages based on ``request`` parameters.
        '''
        raise NotImplementedError('🚨 Subclasses must implement ``faceted_markup`` if they desire faceted nav')

    def serve(self, request: HttpRequest) -> HttpResponse:
        '''Overridden service.

        We override serve in order to handle faceted navigation: when ``ajax`` is ``true``, we return
        just the faceted results, marked up. Otherwise we service the request normally. Subclasses
        won't need to override this usually.
        '''
        if request.GET.get('ajax') == 'true':
            # Since we moved everything to DataTables, this is no longer used.
            return HttpResponse(self.faceted_markup(request))
        elif request.GET.get('ajax') == 'json':
            # This is used by DataTables for client-side processing
            return JsonResponse(self.json(request))
        elif request.GET.get('ajax') == 'json-server-datatable':
            # This is used by DataTables for server-side processing
            return JsonResponse(self.json_datatable(request))
        else:
            # Well maybe our superclass knows how to handle this 🤷‍♀️
            return super().serve(request)

    def _get_server_side_search_columns(self, qd: QueryDict) -> tuple:
        '''From the given ``qd``, determine all the desired columns and their search parameters,
        and all the desired column orderings. Return a double of lists. The first list in the
        double tells all the desired columns in priority order and consists of
        ``DataTableColumn`` objects. The second list in the double tells how the data should be
        ordered and consists of ``DataTableOrdering`` objects.
        '''
        columns, orderings = {}, {}
        for key, values in _request_parameters(qd):
            if key.startswith('order'):
                match = _order_regex.match(key)
                if match:
                    priority = int(match.group(1))
                    ordering = orderings.get(priority, DataTableOrdering(priority))
                    if match.group(2) == 'column':
                        ordering.column = int(values[0])
                    elif match.group(2) == 'dir':
                        ordering.ascending = values[0] == 'asc'
                    orderings[priority] = ordering
                else:
                    _logger.warning('DataTables passed an order directive I cannot parse: «%s»', key)
            elif key.startswith('column'):
                match = _col_regex.match(key)
                if match:
                    priority, kind = int(match.group(1)), match.group(2)
                    column = columns.get(priority, DataTableColumn(priority))
                    if kind == 'data':
                        column.data = values[0]
                    elif kind == 'name':
                        column.name = values[0]
                    elif kind == 'searchable':
                        column.searchable = values[0] == 'true'
                    elif kind == 'orderable':
                        column.orderable = values[0] == 'true'
                    elif kind == 'search':
                        search_param = match.group(4)
                        if search_param == 'value':
                            column.search_value = values[0]
                        elif search_param == 'regex':
                            column.search_regex = values[0] == 'true'
                    columns[priority] = column
                else:
                    _logger.warning('DataTables passed a column directive I cannot parse: «%s»', key)
        return sorted(columns.values()), sorted(orderings.values())

    def get_server_side_datatable_results(
        self, search_value: str, columns: list[DataTableColumn], orderings: list[DataTableOrdering]
    ) -> list[dict]:
        '''Get the datatable results for the given search parameters and return them as a
        list of dicts describing each matching row. Subclasses are strongly encouraged to
        memoize their implementations.
        '''
        raise NotImplementedError('Sublcasses must implement ``get_server_side_datatable_results``')

    def json_datatable(self, request: HttpRequest) -> dict:
        '''Return a json-ready package for server-side DataTables.

        Sadly we can't do this quite yet since Elasticsearch can't order columns. See
        wagtail/wagtail#5319 for more information.
        '''
        g = request.GET.copy()
        draw, start, length = int(g.pop('draw')[0]), int(g.pop('start')[0]), int(g.pop('length')[0])
        search_value, search_regex = g.pop('search[value]')[0], g.pop('search[regex]')[0] == 'true'
        columns, orderings = self._get_server_side_search_columns(g)

        # Elasticsearch supports regex searching but the Wagtail search interface to it does not.
        # So check to see if any regex search is enabled; if so, we can't do it.
        if search_regex or any([i.search_regex for i in columns]):
            raise ValueError('We cannot support regex searches at this time')

        results = self.get_server_side_datatable_results(search_value, search_regex, columns, orderings)
        return {
            'draw': draw,
            'recordsTotal': self.get_contents(request).count(),
            'recordsFiltered': len(results),
            'data': results[start:length]
        }

        # 'ajax': ['json-server-datatable']
        # 'draw': ['1']
        # 'columns[0][data]': ['title']
        # 'columns[0][name]': ['']
        # 'columns[0][searchable]': ['true']
        # 'columns[0][orderable]': ['true']
        # 'columns[0][search][value]': ['']
        # 'columns[0][search][regex]': ['false']
        # 'columns[1][data]': ['journal']
        # 'columns[1][name]': ['']
        # 'columns[1][searchable]': ['true']
        # 'columns[1][orderable]': ['true']
        # 'columns[1][search][value]': ['']
        # 'columns[1][search][regex]': ['false']
        # 'columns[2][data]': ['year']
        # 'columns[2][name]': ['']
        # 'columns[2][searchable]': ['true']
        # 'columns[2][orderable]': ['true']
        # 'columns[2][search][value]': ['']
        # 'columns[2][search][regex]': ['false']
        # 'order[0][column]': ['0']
        # 'order[0][dir]': ['asc']
        # 'start': ['0']
        # 'length': ['10']
        # 'search[value]': ['']
        # 'search[regex]': ['false']
        # '_': ['1669931867747']

    def json(self, request: HttpRequest) -> HttpResponse:
        data = [i.data_table() for i in self.get_contents(request)]
        return {'data': data}

    def get_contents(self, request: HttpRequest) -> object:
        '''Get my knowledge objects.

        This returns the contained KnowledgeObjects (down to their specifics) as either a ``PageQuerySet``
        or as ``SearchResults``. Subclasses that do faceted refinement might do the latter by overriding
        this method and applying the constraints dictated by the ``request``. By default, we just
        return the child pages that are live and public.
        '''
        return KnowledgeObject.objects.child_of(self).live().public().specific().order_by(Lower('title'))

    def get_context(self, request: HttpRequest, *args, **kwargs) -> dict:
        '''Get the context for the page template.'''
        context = super().get_context(request, args, kwargs)

        # Get our contents
        contents = self.get_contents(request)
        context['knowledge_objects'] = contents
        context['knowledge_empty'] = contents.count() == 0

        # Preserve any ``query`` parameter; some knowlege folders don't even use this
        query = request.GET.get('query')
        if query: context['query'] = query

        # Done
        return context

    class Meta:
        ordering = ['ingest_order']
    class RDFMeta:
        ingestor = 'eke.knowledge.utils.Ingestor'
        types = {}


class RDFSource(Orderable):
    '''A single source of RDF.'''
    name   = models.CharField(max_length=255, blank=False, null=False, default='Some RDF Source')
    url    = models.URLField(max_length=MAX_URI_LENGTH, blank=False, null=False, default='https://some.source/rdf')
    active = models.BooleanField(default=True, help_text='Toggle whether to use this source')
    page   = ParentalKey(KnowledgeFolder, on_delete=models.CASCADE, related_name='rdf_sources')
    panels = [FieldPanel('name'), FieldPanel('url'), FieldPanel('active')]
    def __str__(self):
        return f'{self.name} @ {self.url}'
