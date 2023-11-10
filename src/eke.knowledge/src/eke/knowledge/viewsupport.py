# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: models supporting views and forms.'''

from django.http import HttpRequest, HttpResponse
from wagtail.models import Page


class MemberFinderPage(Page):
    '''A page that holds the member finder view.'''
    search_auto_update = False
    page_description = 'A page that holds the Member Finder'
    subpage_types = []

    class Meta:
        pass

    def serve(self, request: HttpRequest) -> HttpResponse:
        '''Let the member finder view handle this.'''
        from .views import find_members
        return find_members(request)
