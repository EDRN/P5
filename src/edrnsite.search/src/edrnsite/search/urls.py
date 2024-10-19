# encoding: utf-8

'''🔍 EDRN Site Search: URL patterns.'''

from .views import search, search_summary
from django.urls import re_path

urlpatterns = [
    re_path(r'^search/$', search, name='search'),
    re_path(r'^summarize/$', search_summary, name='summarize')
]
