# encoding: utf-8

'''🔍 EDRN Site Search: views.'''

from django.core.paginator import Paginator, InvalidPage
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from edrnsite.controls.models import Search
from wagtail.contrib.search_promotions.models import Query, SearchPromotion
from wagtail.models import Page
from io import StringIO
from openai import OpenAI
from markdown import markdown


# Which is better?

# _system_prompt = '''You are a helpful assistant to the Early Detection Research Network summarizing search results.
# You can build on the summary based on what you know about the Early Detection Research Network.'''
_system_prompt = '''You are a helpful assistant to the Early Detection Research Network summarizing search results.'''


def search(request):
    '''Extremely basic search.'''
    query = request.GET.get('query')
    if query:
        promotions = Query.get(query).editors_picks.all()
        results = Page.objects.live().autocomplete(query)
        if not results:
            results = Page.objects.live().search(query)
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


def _add_description(prompt: StringIO, page: Page):
    for label, attribute in (
        ('Abstract', 'abstract'),
        ('Description', 'description'),
        ('Description', 'search_description')
    ):
        value = getattr(page, attribute, None)
        if value:
            prompt.write(f'{label}: {value[:200]}\n')
            return


def search_summary(request):
    '''AI summary of the search results.'''
    query = request.GET.get('query')
    if not query:
        return HttpResponse('<p>Sorry, no summary available for no query.</p>', content_type='text/html')

    results = Page.objects.live().autocomplete(query)
    if not results:
        results = Page.objects.live().search(query)
    if not results:
        return HttpResponse('<p>Sorry, no summary available for the given query.</p>', content_type='text/html')

    prompt = StringIO('Summarize the following search results:\n')
    for result in results:
        prompt.write(f'Title: {result.title}\n')
        _add_description(prompt, result.specific)
        prompt.write('\n')

    client, markdown_response = OpenAI(api_key=settings.OPEN_AI_API_KEY), StringIO()
    ai_response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': _system_prompt},
            {'role': 'user', 'content': prompt.getvalue()}
        ],
        stream=True
    )
    for chunk in ai_response:
        if chunk.choices[0].delta.content is not None:
            markdown_response.write(chunk.choices[0].delta.content)
    return HttpResponse(markdown(markdown_response.getvalue()), content_type='text/html')
