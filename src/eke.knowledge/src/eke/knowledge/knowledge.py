# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: classes to represent the base level of knowledge.'''

from .constants import MAX_URI_LENGTH
from .rdf import RDFAttribute
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.http import HttpRequest
from django.http import HttpResponse, JsonResponse
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.models import Page, Orderable
from wagtailmetadata.models import MetadataPageMixin
from wagtail.search import index
import rdflib


class KnowledgeObject(MetadataPageMixin, Page):
    '''An object in a knowledge environment that has an RDF subject URI.'''
    template = 'eke.knowledge/knowledge-object.html'
    search_auto_update = True

    # I'd like this to be the primary_key for the table but Wagtail expects integers 🤷‍♀️
    identifier = models.CharField(
        'subject URI',
        blank=False, null=False, primary_key=False, unique=True, max_length=MAX_URI_LENGTH,
        help_text='RDF subject URI that uniquely identifies this object',
    )
    description = models.TextField(blank=True, null=False, help_text='A summary or descriptive abstract')

    content_panels = Page.content_panels + [FieldPanel('identifier'), FieldPanel('description')]
    search_fields = Page.search_fields + [index.SearchField('description')]

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


class KnowledgeFolder(MetadataPageMixin, Page):
    '''A container for Knowledge Objects.'''

    ingest         = models.BooleanField(default=True, help_text='Enable or disable ingest for this folder')
    ingest_order   = models.IntegerField(blank=False, null=False, default=0, help_text='Relative ordering of ingest')
    subpage_types  = [KnowledgeObject]
    template       = 'eke.knowledge/knowledge-folder.html'
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
            return HttpResponse(self.faceted_markup(request))
        elif request.GET.get('ajax') == 'json':
            return JsonResponse(self.json(request))
        else:
            return super().serve(request)

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
