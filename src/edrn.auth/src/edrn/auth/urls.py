# encoding: utf-8

'''🔐 EDRN auth: URL patterns.'''

from django.urls import path
from .views import LogoutView


urlpatterns = [
    path('logout/', LogoutView.as_view(), name='logout'),
]
