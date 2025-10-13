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
from markdown import markdown
from urllib.parse import urlencode, urljoin
import boto3, json, logging

_logger = logging.getLogger(__name__)


def search(request):
    '''Extremely basic search.'''
    query = request.GET.get('query')
    _logger.info('🔎 Search query: %s', query)
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
        'query': query, 'page': page, 'ranger': ranger, 'promotions': promotions, 'num_promotions': len(promotions),
        'when_to_enable_ai': controls.when_to_enable_ai
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
    controls = Search.for_request(request)

    # Hard-coding the model because in testing this gives us the best results and can access external
    # resources. None of the others hold up.
    model = 'us.amazon.nova-pro-v1:0'
    system_list = [{'text': controls.system_prompt}]

    # Deployment issue: we need the AI to retrieve the results from "the portal", but which instance?
    # In development, this is on my Mac Studio. On the testing site, it's behind a firewall at JPL. And
    # at NCI it's either edrn-dev (inaccessible), edrn-stage (inaccessble), or edrn.nci.nih.gov—but
    # that's the production site.
    #
    # We may as well use the production site!

    url = urljoin('https://edrn.nci.nih.gov/search/', '?' + urlencode({'query': query}))
    prompt = f'Please visit the search results at url {url} and summarize the results in Markdown format.'
    message_list = [{'role': 'user', 'content': [{'text': prompt}]}]
    inf_params = {'max_new_tokens': 1000, 'top_p': 0.9, 'top_k': 20, 'temperature': 0.7}
    request_body = {
        'schemaVersion': 'messages-v1',
        'messages': message_list,
        'system': system_list,
        'inferenceConfig': inf_params
    }

    # JPL does not allow us to use Bedrock outside of VPN; so I could try to build this app on the JPL
    # MacBook Pro, but it requires tools that aren't available in JAMF Software Center.
    #
    # But using my user-based role I can access Bedrock anywhere, so when in debug mode (when I'm
    # developing), I can first use the aws-login application and have it give the bedrock-runtime
    # service.
    #
    # At JPL, debug mode is off, and then it can use the regular `SRV-edrn-dev-bedrock-app-backend`
    # access key and secret key.

    if settings.DEBUG:
        session = boto3.Session(profile_name='saml-pub')
        bedrock_runtime = session.client(service_name='bedrock-runtime')
    else:
        bedrock_runtime = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=controls.bedrock_access_key, aws_secret_access_key=controls.bedrock_secret_key,
            region_name=controls.bedrock_region
        )

    # Thinking machines
    response = bedrock_runtime.invoke_model(modelId=model, body=json.dumps(request_body))
    model_response = json.loads(response['body'].read())
    response_text = model_response['output']['message']['content'][0]['text']
    return HttpResponse(markdown(response_text), content_type='text/html')
