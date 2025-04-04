# encoding: utf-8

'''👥 EDRN Collaborative Groups: models.'''

from datetime import datetime, timezone
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.http import HttpRequest
from edrnsite.content.models import FlexPage
from edrnsite.streams import blocks
from eke.knowledge.models import Person
from eke.knowledge.utils import aware_now
from modelcluster.fields import ParentalManyToManyField
from wagtail.admin.panels import FieldPanel
from wagtail import blocks as wagtail_core_blocks
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.snippets.models import register_snippet
import zoneinfo


@register_snippet
class CollaborativeGroupSnippet(models.Model):
    '''A collaborative group.'''
    cg_code = models.CharField(max_length=10, blank=False, null=False, unique=True)
    name = models.CharField(max_length=80, blank=False, null=False, unique=True)
    panels = [FieldPanel('cg_code'), FieldPanel('name')]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Collaborative Group Snippet'
        verbose_name_plural = 'Collaborative Group Snippets'


class CommitteeEvent(Page):
    '''An event happening for a committee.'''
    template = 'edrn.collabgroups/committee-event.html'
    search_auto_update = False
    parent_page_types = ['edrncollabgroups.Committee']
    page_description = 'Event for a committee'
    subpage_types = []

    LOS_ANGELES = 'America/Los_Angeles'
    DENVER      = 'America/Denver'
    CHICAGO     = 'America/Chicago'
    NEW_YORK    = 'America/New_York'
    UTC         = 'UTC'
    TIMEZONE_CHOICES = [
        (LOS_ANGELES, 'Los Angeles (pacific)'),
        (DENVER, 'Denver (mountain)'),
        (CHICAGO, 'Chicago (central)'),
        (NEW_YORK, 'New York (eastern)'),
        (UTC, 'UTC (global)'),
    ]

    when = models.DateTimeField(help_text='When does this event start; will be converted to UTC based on timezone below')
    timezone = models.CharField(
        max_length=19, choices=TIMEZONE_CHOICES, default=NEW_YORK, help_text='Timezone of this event'
    )
    online_meeting_url = models.URLField(
        blank=True,
        help_text='URL to online event; please remove any "URL-defense" before pasting in a URL',
        max_length=2000
    )
    body = StreamField([
        ('rich_text', wagtail_core_blocks.RichTextBlock(
            label='Rich Text',
            icon='doc-full',
            help_text='Richly formatted text',
        )),
        ('cards', blocks.CardsBlock()),
        ('table', blocks.TableBlock()),
        ('carousel', blocks.CarouselBlock()),
    ], null=True, blank=True, use_json_field=True, help_text='Body text of this event')

    def clean(self):
        super().clean()

        # The time as entered from the browser is always UTC because our application settings stipulate
        # the timezone as UTC. But if the user selected a different timezone, convert it to the chosen
        # one and then convert that to UTC.
        if self.when is None:
            # Time hasn't been entered yet, so done
            return

        if self.timezone == self.UTC:
            # Time's already in UTC, so done
            return

        selected_tz = zoneinfo.ZoneInfo(self.timezone)
        when = datetime(
            self.when.year, self.when.month, self.when.day, self.when.hour, self.when.minute, self.when.second,
            tzinfo=selected_tz
        )
        self.when, self.timezone = when.astimezone(timezone.utc), self.UTC

    # def get_context(self, request: HttpRequest, *args, **kwargs) -> dict:
    #     context = super().get_context(request, *args, **kwargs)
    #     return context

    content_panels = Page.content_panels + [
        FieldPanel('when'),
        FieldPanel('timezone'),
        FieldPanel('online_meeting_url'),
        FieldPanel('body'),
    ]


class Committee(Page):
    '''A committee is a group of people with a chair, co-chair, and members. It also has
    events and documents.
    '''
    template = 'edrn.collabgroups/committee.html'
    search_auto_update = False
    subpage_types = [FlexPage, CommitteeEvent]
    page_description = 'Collaborative group, committee, working group, etc.'

    id_number = models.CharField(blank=True, max_length=10, help_text='DMCC-assigned identification number')
    description = models.TextField(blank=True, null=False, help_text='A summary or descriptive abstract')
    documents_heading = models.TextField(
        blank=False, default='Documents', help_text='What should the heading above the documents/agendas be?'
    )
    chair = models.ForeignKey(
        Person, null=True, blank=True, verbose_name='Chair', related_name='committees_I_chair',
        on_delete=models.SET_NULL
    )
    co_chairs = ParentalManyToManyField(
        Person, blank=True, verbose_name='Co-Chair(s)', related_name='committees_I_co_chair'
    )
    members = ParentalManyToManyField(
        Person, blank=True, verbose_name='Members', related_name='committees_I_belong_to'
    )
    program_officers = ParentalManyToManyField(
        Person, blank=True, verbose_name='Program Officers', related_name='committees_I_officiate'
    )
    project_scientists = ParentalManyToManyField(
        Person, blank=True, verbose_name='Project Scientists', related_name='committess_I_do_science_for'
    )

    content_panels = Page.content_panels + [
        FieldPanel('id_number'),
        FieldPanel('description'),
        FieldPanel('documents_heading'),
        FieldPanel('chair'),
        FieldPanel('co_chairs'),
        FieldPanel('members'),
        FieldPanel('program_officers'),
        FieldPanel('project_scientists'),
    ]

    def get_context(self, request: HttpRequest, *args, **kwargs) -> dict:
        context = super().get_context(request, args, kwargs)

        event_content_type = ContentType.objects.filter(app_label='edrncollabgroups', model='committeeevent').first()
        assert event_content_type is not None

        context = super().get_context(request, *args, **kwargs)
        context['members'] = self.members.all().order_by('title')

        now = aware_now()
        future = CommitteeEvent.objects.child_of(self).filter(when__gte=now).live().order_by('-when')
        past = CommitteeEvent.objects.child_of(self).filter(when__lte=now).live().order_by('-when')
        have_events = future.count() > 0 or past.count() > 0
        docs = self.get_children().exclude(content_type=event_content_type).live().all()

        context['future_events'], context['past_events'], context['have_events'] = future, past, have_events
        context['documents'] = docs

        return context
