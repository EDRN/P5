# encoding: utf-8

'''🧬 EDRN Site: meta descriptions.'''

from django.core.management.base import BaseCommand
from edrn.collabgroups.models import Committee, CommitteeEvent
from edrnsite.content.models import FlexPage
from eke.biomarkers.models import Biomarker
from eke.knowledge.models import BodySystem, Disease, OrganizationalGroup, MiscellaneousResource


class Command(BaseCommand):
    '''The EDRN "meta descrptions" command".'''

    help = 'Add meta descriptions to various objects'

    def handle(self, *args, **options):
        '''Handle the EDRN `edrn_meta_descs` command.'''

        self.stdout.write('Adding meta descs to biomarkers')
        count = Biomarker.objects.all().count()
        for biomarker in Biomarker.objects.all():
            if not biomarker.search_description:
                biomarker.search_description = biomarker.description
                biomarker.save()
            del biomarker
            count -= 1
            if count % 100 == 0 and count > 0:
                self.stdout.write(f'{count} biomarkers to go')

        self.stdout.write('Adding meta descs to body systems')
        for bs in BodySystem.objects.all():
            if not bs.search_description:
                bs.search_description = f'The {bs.title.lower()} is an organ of the human body'
                bs.save()
            del bs

        self.stdout.write('Adding meta descs to diseases')
        for d in Disease.objects.all():
            if not d.search_description:
                d.search_description = f'{d.title} is an ailment of the human body'
                d.save()
            del d

        self.stdout.write('Adding meta descs to committees')
        for c in Committee.objects.all():
            if not c.search_description:
                if c.description == 'No description available.':
                    c.search_description = f'The {c.title} is a commitee, group, or other organizational unit of the Early Detection Research Network.'
                else:
                    c.search_description = c.description
                c.save()
            del c

        self.stdout.write('Adding meta descs to organizational groups')
        for o in OrganizationalGroup.objects.all():
            if not o.search_description:
                o.search_description = f'This is a group in EDRN called "{o.title}"'
                o.save()
            del o

        self.stdout.write('Adding meta descs to committee events')
        for e in CommitteeEvent.objects.all():
            if not e.search_description:
                e.search_description = f'This was an event held on {e.when.date().isoformat()}'
                e.save()
            del e

        self.stdout.write('Adding meta descs to misc resources')
        count = MiscellaneousResource.objects.all().count()
        for m in MiscellaneousResource.objects.all():
            if not m.search_description:
                m.search_description = f'This is a miscellaneous resource located at {m.identifier}'
                m.save()
            del m
            count -= 1
            if count % 100 == 0 and count > 0:
                self.stdout.write(f'{count} miscellaneous resources to go')

        self.stdout.write('Adding meta descs to flex pages with recurring themes: group calls')
        for page in FlexPage.objects.filter(title__contains='Group Call'):
            if not page.search_description:
                page.search_description = 'This was a group call held in the past'
                page.save()
            del page
        self.stdout.write('Adding meta descs to flex pages with recurring themes: conference calls')
        for page in FlexPage.objects.filter(title__contains='Conference Call'):
            if not page.search_description:
                page.search_description = 'This was a conference call held in the past'
                page.save()
            del page
        self.stdout.write('Adding meta descs to flex pages with recurring themes: ending with "Call"')
        for page in FlexPage.objects.filter(title__endswith='Call'):
            if not page.search_description:
                page.search_description = 'This was a call held in the past'
                page.save()
            del page
        self.stdout.write('Adding meta descs to flex pages with recurring themes: Group Meetings')
        for page in FlexPage.objects.filter(title__contains='Group Meeting'):
            if not page.search_description:
                page.search_description = 'This was a group meeting held in the past'
                page.save()
            del page
        self.stdout.write('Adding meta descs to flex pages with recurring themes: workshop')
        for page in FlexPage.objects.filter(title__contains='Workshop'):
            if not page.search_description:
                page.search_description = 'This was a workshop held in the past'
                page.save()
            del page
        self.stdout.write('Adding meta descs to flex pages with recurring themes: meeting')
        for page in FlexPage.objects.filter(title__contains='Meeting'):
            if not page.search_description:
                page.search_description = 'This was a meeting held in the past'
                page.save()
            del page
        self.stdout.write('Adding meta descs to flex pages with recurring themes: Meeting')
        for page in FlexPage.objects.filter(title__contains='meeting'):
            if not page.search_description:
                page.search_description = 'This was a meeting held in the past'
                page.save()
            del page
        self.stdout.write('Adding meta descs to flex pages with recurring themes: webinar')
        for page in FlexPage.objects.filter(title__contains='webinar'):
            if not page.search_description:
                page.search_description = 'This was a web-based seminar held in the past'
                page.save()
            del page
        self.stdout.write('Adding meta descs to flex pages with recurring themes: teleconference')
        for page in FlexPage.objects.filter(title__contains='Teleconference'):
            if not page.search_description:
                page.search_description = 'This was a telephone conference held in the past'
                page.save()
            del page
        self.stdout.write('Adding meta descs to flex pages with recurring themes: agenda')
        for page in FlexPage.objects.filter(title__contains='Agenda'):
            if not page.search_description:
                page.search_description = 'This is the list of items, schedule, program, timetable, or plan for a meeting'
                page.save()
            del page
        self.stdout.write('Adding meta descs to flex pages with recurring themes: ending with presentations')
        for page in FlexPage.objects.filter(title__endswith='Presentations'):
            if not page.search_description:
                page.search_description = 'These are materials made for a meeting, usually in the form of visual slides'
                page.save()
            del page
        self.stdout.write('Adding meta descs to flex pages with recurring themes: ending with materials')
        for page in FlexPage.objects.filter(title__endswith='Materials'):
            if not page.search_description:
                page.search_description = 'These are materials made for a meeting'
                page.save()
            del page
