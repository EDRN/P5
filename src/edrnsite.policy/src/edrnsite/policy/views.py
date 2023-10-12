# encoding: utf-8

'''🧬 EDRN Site Policy: views.'''

from django.core.cache import caches
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from edrn.auth.views import logged_in_or_basicauth


def _get_referrer(request: HttpRequest) -> str:
    try:
        return request.META['HTTP_REFERER']
    except KeyError:
        return '/'


@logged_in_or_basicauth('edrn')
def clear_caches(request: HttpRequest) -> HttpResponse:
    '''Clear all caches.'''
    if request.user.is_staff or request.user.is_superuser:
        for cache in caches:
            caches[cache].clear()
        return HttpResponseRedirect(_get_referrer(request))
    else:
        return HttpResponseForbidden()
