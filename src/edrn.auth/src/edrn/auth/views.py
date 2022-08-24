# encoding: utf-8

'''🔐 EDRN auth: views.'''

from django.contrib.auth import views as auth_views
from django.http import HttpRequest, HttpResponse
from django.contrib import messages
from django.conf import settings


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
