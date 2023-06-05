# encoding: utf-8

'''🔐 EDRN Auth: tests for views.'''


from wagtail.test.utils import WagtailPageTestCase
from django.urls import reverse


class AuthTests(WagtailPageTestCase):
    def setUp(self):
        self.user = self.create_test_user()

    def test_logout_view(self):
        '''Ensure the logout view logs you out'''

        # First, log in
        post = {'username': 'test@email.com', 'password': 'password', 'next': '/'}
        self.client.post(reverse('wagtailcore_login'), post)
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, '/_util/login/')
