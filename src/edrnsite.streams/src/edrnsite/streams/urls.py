# encoding: utf-8

'''🦦 EDRN Site streams: URLs.'''


from .views import update_data_element_explorers
from django.urls import path


urlpatterns = [
    path('update_data_element_explorers', update_data_element_explorers, name='update_data_element_explorers'),
]
