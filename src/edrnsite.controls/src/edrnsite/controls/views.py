# encoding: utf-8

'''🎛 EDRN Site Controls: views.'''

from .tasks import do_update_my_ip
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from edrn.auth.views import logged_in_or_basicauth


def _get_referrer(request: HttpRequest) -> str:
    try:
        return request.META['HTTP_REFERER']
    except KeyError:
        return '/'


@logged_in_or_basicauth('edrn')
def update_my_ip(request: HttpRequest) -> HttpResponse:
    '''Update my IP address.'''
    if request.user.is_staff or request.user.is_superuser:
        do_update_my_ip.delay()
        return HttpResponseRedirect(_get_referrer(request))
    else:
        return HttpResponseForbidden()
