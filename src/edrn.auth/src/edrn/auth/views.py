# encoding: utf-8

'''🔐 EDRN auth: views.'''

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
import base64, http


def authentication_context(request) -> dict:
    '''Give the dictionary of authentication-related context for use in a page template.'''
    return {
        'authenticated': request.user.is_authenticated,
        'logout': reverse('logout') + '?next=' + request.path,
        # The "login" page is the full login with all the alternative destinations
        'login': reverse('wagtailcore_login') + '?next=' + request.path,
        # The "portal_login" page has just portal-related login, no alternative destinations like the
        # "secure" site or LabCAS.
        'portal_login': reverse('portal_login') + '?next=' + request.path,
    }


def view_or_basicauth(view, request: HttpRequest, test_func, realm: str = '', *args, **kwargs):
    '''Check if a user is logged in or not or if there's HTTP basic authentication.

    Adapted from https://github.com/m7v8/django-basic-authentication-decorator
    '''
    if test_func(request.user):
        return view(request, *args, **kwargs)
    if 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(auth) == 2:
            if auth[0].lower() == "basic":
                uname, passwd = base64.b64decode(auth[1]).decode('utf-8').split(':', 1)
                user = authenticate(username=uname, password=passwd)
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        request.user = user
                        if test_func(request.user):
                            return view(request, *args, **kwargs)
    response = HttpResponse()
    response.status_code = http.HTTPStatus.UNAUTHORIZED
    response['WWW-Authenticate'] = f'Basic realm="{realm}"'
    return response


def logged_in_or_basicauth(realm: str = ''):
    '''Decorate a view so that it requires a logged-in user or HTTP basic auth to be present.''

    Adapated from https://github.com/m7v8/django-basic-authentication-decorator
    '''
    def view_decorator(func):
        def wrapper(request, *args, **kwargs):
            return view_or_basicauth(func, request, lambda u: u.is_authenticated, realm, *args, **kwargs)
        return wrapper
    return view_decorator


@logged_in_or_basicauth('edrn')
def authentication_test_view(request: HttpRequest) -> HttpResponse:
    '''A basic view that just simply requires you to be logged in and returns an empty payload.'''
    response = HttpResponse('')
    response.status_code = http.HTTPStatus.OK
    return response


class LogoutView(auth_views.LogoutView):
    next_page = 'wagtailcore_login'

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        response = super().dispatch(request, *args, **kwargs)
        messages.success(self.request, "You're logged out. Feel free to log in again.")
        response.delete_cookie(
            settings.SESSION_COOKIE_NAME, domain=settings.SESSION_COOKIE_DOMAIN, path=settings.SESSION_COOKIE_PATH
        )
        self.request.session.modified = False
        return response
