# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: base knowledge URL patterns.'''


from .views import start_full_ingest, reindex_all_content, sync_ldap_groups, dispatch_data, find_members, fix_tree
from django.urls import path, include


urlpatterns = [
    path('start_full_ingest', start_full_ingest, name='start_full_ingest'),
    path('reindex_all_content', reindex_all_content, name='reindex_all_content'),
    path('fixtree', fix_tree, name='fixtree'),
    path('sync_ldap_groups', sync_ldap_groups, name='sync_ldap_groups'),
    path('django_plotly_dash/', include('django_plotly_dash.urls')),
    path('@@dataDispatch', dispatch_data, name='dispatch_data'),
    path('find-members', find_members, name='find-members'),
]
