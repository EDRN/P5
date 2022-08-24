# encoding: utf-8

'''🔍 EDRN Site Search: views.'''

from django.shortcuts import render
from wagtail.models import Page
from wagtail.search.models import Query
from django.core.paginator import Paginator, InvalidPage
from edrnsite.controls.models import Search


def search(request):
    '''Extremely basic search.'''
    query = request.GET.get('query')
    if query:
        results = Page.objects.live().search(query)
        Query.get(query).add_hit()
    else:
        results = Page.objects.none()
    controls = Search.for_request(request)
    paginator = Paginator(results, controls.results_per_page, controls.orphans)
    try:
        pageNum = int(request.GET.get('page'))
        page = paginator.page(pageNum)
    except (ValueError, TypeError):
        pageNum = 1
        page = paginator.page(pageNum)
    except InvalidPage:
        pageNum = paginator.num_pages
        page = paginator.page(pageNum)
    ranger = paginator.get_elided_page_range(pageNum, on_each_side=controls.surrounding, on_ends=controls.ends)
    context = {'query': query, 'page': page, 'ranger': ranger}
    return render(request, 'edrnsite.search/search.html', context)
