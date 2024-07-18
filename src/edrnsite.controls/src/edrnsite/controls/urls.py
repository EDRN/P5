# encoding: utf-8

'''🎛 EDRN Site Controls: URL patterns.'''


from .views import update_my_ip
from django.urls import path


urlpatterns = [
    path('update_my_ip', update_my_ip, name='update_my_ip'),
]
