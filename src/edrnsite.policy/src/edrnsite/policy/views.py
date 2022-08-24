# encoding: utf-8

'''🧬 EDRN Site Policy: views.'''

from django.core.cache import caches
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, HttpResponseForbidden


def clear_caches(request: HttpRequest) -> HttpResponse:
    '''Clear all caches.'''
    if request.user.is_superuser:
        for cache in caches:
            caches[cache].clear()
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        return HttpResponseForbidden()
