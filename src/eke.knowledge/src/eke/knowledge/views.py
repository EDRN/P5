# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: views.'''

from .knowledge import KnowledgeObject
from .tasks import do_full_ingest, do_reindex, do_ldap_group_sync
from .sites import Site, Person
from edrn.auth.views import logged_in_or_basicauth
from django.shortcuts import render
from django.db.models import Q
from django.db.models.functions import Lower
from django.http import (
    HttpRequest, HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotFound, HttpResponseBadRequest
)


def _get_referrer(request: HttpRequest) -> str:
    try:
        return request.META['HTTP_REFERER']
    except KeyError:
        return '/'


@logged_in_or_basicauth('edrn')
def start_full_ingest(request: HttpRequest) -> HttpResponse:
    '''Start a full ingest and redirect to our referrer.''' 
    if request.user.is_superuser:
        do_full_ingest.delay()
        return HttpResponseRedirect(_get_referrer(request))
    else:
        return HttpResponseForbidden()


@logged_in_or_basicauth('edrn')
def reindex_all_content(request: HttpRequest) -> HttpResponse:
    '''Reindex all content on the site and redirect to our referrer.'''
    if request.user.is_superuser:
        do_reindex.delay()
        return HttpResponseRedirect(_get_referrer(request))
    else:
        return HttpResponseForbidden()


@logged_in_or_basicauth('edrn')
def sync_ldap_groups(request: HttpRequest) -> HttpResponse:
    '''Synchronize all LDAP groups into Django groups.'''
    if request.user.is_superuser:
        do_ldap_group_sync.delay()
        return HttpResponseRedirect(_get_referrer(request))
    else:
        return HttpResponseForbidden()


def dispatch_data(request: HttpRequest) -> HttpResponse:
    '''Map an RDF subject URI to its matching page in the portal.'''
    subject_uri = request.GET.get('subjectURI')
    if subject_uri is None or len(subject_uri) == 0:
        return HttpResponseBadRequest(reason='The subjectURI parameter is required')
    match = KnowledgeObject.objects.filter(identifier__exact=subject_uri).first()
    if match is None:
        return HttpResponseNotFound(reason='The subject with the given URI was not found')
    else:
        return HttpResponseRedirect(match.url)


def find_members(request: HttpRequest) -> HttpResponse:
    '''Member finder view.

    This handles rendering of the member finder page and also the faceted re-visit as the
    user makes selections.
    '''    
    if request.GET.get('ajax') == 'true':
        pi, site_name, types = request.GET.get('pi'), request.GET.get('site'), request.GET.getlist('member-type')

        if pi or site_name or types:
            site_filter = {}
            if pi: site_filter['pi'] = Person.objects.filter(title__exact=pi).first()
            if site_name: site_filter['title__exact'] = site_name
            if types: site_filter['memberType__in'] = types
            sites = Site.objects.filter(Q(**site_filter)).live().public().order_by(Lower('title')).order_by('dmccSiteID')
        else:
            sites = Site.objects.none()

        results, num_sites, num_people = [], 0, 0
        for site in sites:
            people = Person.objects.child_of(site).live().public().order_by(Lower('title'))
            num_sites += 1
            num_people += people.count()
            results.append({'site': site, 'people': people})

        rendering = {'results': results, 'num_sites': num_sites, 'num_people': num_people}
        return render(request, 'eke.knowledge/member-finder-results.html', rendering)

    else:
        return render(request, 'eke.knowledge/member-finder.html', {})

    # if query:
    #     results = Page.objects.live().search(query)
    #     Query.get(query).add_hit()
    # else:
    #     results = Page.objects.none()
    # controls = Search.for_request(request)
