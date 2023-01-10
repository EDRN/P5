# encoding: utf-8

'''📐 EDRN metrics: views.'''


from edrn.auth.views import logged_in_or_basicauth
from django.http import HttpRequest, HttpResponse, HttpResponseServerError, HttpResponseRedirect, HttpResponseForbidden
from .models import ReportIndex, generate_report


def _get_referrer(request: HttpRequest) -> str:
    try:
        return request.META['HTTP_REFERER']
    except KeyError:
        return '/'


@logged_in_or_basicauth('edrn')
def run_report(request: HttpRequest) -> HttpResponse:
    if request.user.is_staff or request.user.is_superuser:
        index = ReportIndex.objects.first()
        if index is None:
            return HttpResponseServerError('No ReportIndex found'.encode('utf-8'))
        report = generate_report(index)
        return HttpResponseRedirect(report.url)
    else:
        return HttpResponseForbidden()
