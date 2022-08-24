# encoding: utf-8

'''🔍 EDRN Site Search: URL patterns.'''

from .views import search
from django.urls import re_path

urlpatterns = [
    re_path(r'^search/$', search, name='search'),
]
