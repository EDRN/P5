# encoding: utf-8

'''🚗 EDRN Knowledge Environment: cars.'''

from .knowledge import KnowledgeObject, KnowledgeFolder
from .rdf import RDFAttribute
from django.db import models
from django.http import HttpRequest
from django.template.loader import render_to_string
from wagtail.admin.panels import FieldPanel
from wagtail.search import index


class Car(KnowledgeObject):
    '''A 🚗.'''
    template = 'eke.knowledge/car.html'
    make = models.CharField(max_length=100, blank=True, null=False)
    model = models.CharField(max_length=100, blank=True, null=False)
    year = models.IntegerField(null=True, blank=True)
    condition = models.CharField(max_length=200, blank=True, null=False)
    color = models.CharField(max_length=15, blank=True, null=False)
    price = models.IntegerField(null=True, blank=True)
    parent_page_types = ['ekeknowledge.CarIndex']
    content_panels = KnowledgeObject.content_panels + [
        FieldPanel('make'),
        FieldPanel('model'),
        FieldPanel('year'),
        FieldPanel('condition'),
        FieldPanel('color'),
        FieldPanel('price'),
    ]
    search_fields = KnowledgeObject.search_fields + [
        index.SearchField('make'),
        index.FilterField('make'),
        index.SearchField('model'),
        index.FilterField('year'),
        index.SearchField('condition'),
        index.FilterField('condition'),
        index.SearchField('color'),
        index.FilterField('color'),
        index.FilterField('price'),
    ]
    class RDFMeta:
        fields = {
            'urn:cars:rdf:predicates:make':      RDFAttribute('make',      scalar=True),
            'urn:cars:rdf:predicates:model':     RDFAttribute('model',     scalar=True),
            'urn:cars:rdf:predicates:year':      RDFAttribute('year',      scalar=True),
            'urn:cars:rdf:predicates:condition': RDFAttribute('condition', scalar=True),
            'urn:cars:rdf:predicates:color':     RDFAttribute('color',     scalar=True),
            'urn:cars:rdf:predicates:price':     RDFAttribute('price',     scalar=True),
            **KnowledgeObject.RDFMeta.fields
        }


class CarIndex(KnowledgeFolder):
    '''A container for 🚗s.'''
    subpage_types = [Car]
    template = 'eke.knowledge/car-index.html'

    def get_contents(self, request: HttpRequest):
        # This seems to work, but if we later call .search().facet() on the results, then it can't find the
        # faceted fields:
        #     matches = self.get_children().live().specific().order_by('title')
        # According to @mattwestcott on Wagtail's Slack, the .specific() only works if we retrieve the
        # results later, and additional queries are run to populate the fields. But faceting on the backend
        # doesn't do that. So we have to do this:

        matches = Car.objects.child_of(self).live().order_by('title')

        make, conditions, colors = request.GET.get('make'), request.GET.getlist('condition'), request.GET.getlist('color')
        if make: matches = matches.filter(make=make)
        if conditions: matches = matches.filter(condition__in=conditions)
        minPrice, maxPrice = request.GET.get('minPrice'), request.GET.get('maxPrice')
        if minPrice: matches = matches.filter(price__gte=minPrice)
        if maxPrice: matches = matches.filter(price__lte=maxPrice)
        if colors: matches = matches.filter(color__in=colors)

        query = request.GET.get('query')
        if query: matches = matches.search(query)

        return matches

    def faceted_markup(self, request):
        pages, cards = self.get_contents(request), []
        for page in pages:
            cards.append(render_to_string('eke.knowledge/car-card.html', {'car': page.specific}))
        return ''.join(cards)

    class RDFMeta:
        ingestor = KnowledgeFolder.RDFMeta.ingestor
        types = {'urn:cars:rdf:types:Car': Car}
