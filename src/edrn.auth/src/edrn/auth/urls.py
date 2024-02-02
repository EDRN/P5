# encoding: utf-8

'''🔐 EDRN auth: URL patterns.'''

from django.urls import path
from .forms import EDRNAuthenticationForm
from .views import LogoutView, authentication_test_view
from django.contrib.auth import views as auth_views
from django.conf import settings

WAGTAIL_FRONTEND_LOGIN_TEMPLATE = getattr(settings, 'WAGTAIL_FRONTEND_LOGIN_TEMPLATE', 'edrn.auth/login.html')


urlpatterns = [
    path('_util/login/', auth_views.LoginView.as_view(
        authentication_form=EDRNAuthenticationForm, template_name=WAGTAIL_FRONTEND_LOGIN_TEMPLATE,
    )),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('authentication-test', authentication_test_view, name='authentication-test'),
    path('_util/portal-login', auth_views.LoginView.as_view(
        authentication_form=EDRNAuthenticationForm, template_name='edrn.auth/portal-login.html'
    ), name='portal_login')
]
