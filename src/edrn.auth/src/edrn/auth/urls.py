# encoding: utf-8

'''🔐 EDRN auth: URL patterns.'''

from django.urls import path
from .views import LogoutView, authentication_test_view


urlpatterns = [
    path('logout/', LogoutView.as_view(), name='logout'),
    path('authentication-test', authentication_test_view, name='authentication-test'),
]
