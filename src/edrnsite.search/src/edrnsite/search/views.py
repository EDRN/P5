# encoding: utf-8

'''🔍 EDRN Site Search: views.'''

from django.core.paginator import Paginator, InvalidPage
from django.shortcuts import render
from edrnsite.controls.models import Search
from wagtail.contrib.search_promotions.models import SearchPromotion
from wagtail.models import Page
from wagtail.search.models import Query


def search(request):
    '''Extremely basic search.'''
    query = request.GET.get('query')
    if query:
        results, promotions = Page.objects.live().search(query), Query.get(query).editors_picks.all()
        Query.get(query).add_hit()
    else:
        results, promotions = Page.objects.none(), SearchPromotion.objects.none()
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
    context = {
        'query': query, 'page': page, 'ranger': ranger, 'promotions': promotions, 'num_promotions': len(promotions)
    }
    return render(request, 'edrnsite.search/search.html', context)
