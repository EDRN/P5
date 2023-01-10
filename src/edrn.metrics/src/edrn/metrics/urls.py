# encoding: utf-8

'''📐 EDRN metrics: URL patterns.'''

from .views import run_report
from django.urls import path


urlpatterns = [
    path('run-data-quality-report', run_report, name='run-data-quality-report')
]
