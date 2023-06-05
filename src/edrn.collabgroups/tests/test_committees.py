# encoding: utf-8

'''👥 EDRN Collaborative Groups: tests for committees.'''


from edrn.collabgroups.models import Committee, CommitteeEvent
from eke.knowledge.utils import aware_now
from wagtail.models import Site as WagtailSite
from wagtail.test.utils import WagtailPageTestCase
from wagtail.test.utils.form_data import nested_form_data, streamfield, rich_text


class CommitteesTests(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        from eke.knowledge.models import Person, Site, SiteIndex

        cls.root_page = WagtailSite.objects.filter(is_default_site=True).first().root_page
        site_index = SiteIndex(title='Site Index')
        cls.root_page.add_child(instance=site_index)
        site_index.save()
        site = Site(title='Site', identifier='urn:test:site')
        site_index.add_child(instance=site)
        site.save()
        cls.person1 = Person(title='Doe, Jo', identifier='urn:test:site:p1')
        site.add_child(instance=cls.person1)
        cls.person1.save()
        cls.person2 = Person(title='Doe, Jane', identifier='urn:test:site:p2')
        site.add_child(instance=cls.person2)
        cls.person2.save()

    def setUp(self):
        self.login()

    def test_committee_location(self):
        '''Ensure commmittees can be created just about anywhere.'''
        from edrnsite.content.models import HomePage
        self.assertCanCreateAt(HomePage, Committee)

    def test_can_create_committee(self):
        '''Ensure we can create a committee.'''
        form = {
            'title': 'My Commmittee', 'description': 'What a nice committee', 'id_number': '123',
            'chair': self.person1.pk, 'co_chair': self.person2.pk,
            'members': [self.person1.pk, self.person2.pk]
        }
        self.assertCanCreate(self.root_page, Committee, nested_form_data(form))

    def test_committee_event_location(self):
        '''Ensure committee events can only be created in committees.'''
        from edrnsite.content.models import HomePage
        self.assertCanNotCreateAt(HomePage, CommitteeEvent)
        self.assertCanCreateAt(Committee, CommitteeEvent)

    def test_can_create_event(self):
        '''Ensure we can create a committee event'''
        committee = Committee(title='My Commmittee')
        self.root_page.add_child(instance=committee)
        form = {
            'title': 'My Event', 'when': aware_now().isoformat(), 'timezone': 'UTC',
            'online_meeting_url': 'https://zoomies.us/123',
            'body': streamfield([('rich_text', rich_text('<p>Be there or be square!</p>'))])
        }
        self.assertCanCreate(committee, CommitteeEvent, nested_form_data(form))
