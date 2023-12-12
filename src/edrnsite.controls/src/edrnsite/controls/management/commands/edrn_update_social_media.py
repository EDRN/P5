'''🎛 EDRN Site Controls: social media update.'''

from django.core.management.base import BaseCommand
from edrnsite.controls.models import SocialMediaLink


class Command(BaseCommand):
    help = 'Updates social media to use the new open-ended links'

    def handle(self, *args, **options):
        self.stdout.write('Updating social media')

        self.stdout.write('Deleting any existing social media')        
        SocialMediaLink.objects.all().delete()

        self.stdout.write('Adding Facebook')
        SocialMediaLink.objects.get_or_create(
            name='Facebook', url='https://www.facebook.com/cancer.gov', bootstrap_icon='facebook'
        )

        self.stdout.write('Adding LinkedIn')
        SocialMediaLink.objects.get_or_create(
            name='LinkedIn', url='https://www.linkedin.com/showcase/cancer-prevention/', bootstrap_icon='linkedin'
        )

        # Supported at NCI, not DCP
        # self.stdout.write('Adding Instagram')
        # SocialMediaLink.objects.get_or_create(
        #     name='Instagram', url='https://www.instagram.com/nationalcancerinstitute/', bootstrap_icon='instagram'
        # )

        # Supported at NCI, not DCP
        # self.stdout.write('Adding YouTube')
        # SocialMediaLink.objects.get_or_create(
        #     name='YouTube', url='https://www.youtube.com/NCIgov', bootstrap_icon='youtube'
        # )

        self.stdout.write('Adding X 🙄')
        SocialMediaLink.objects.get_or_create(
            name='X', url='https://twitter.com/NCIPrevention', bootstrap_icon='twitter-x'
        )

        # Future: include threads and mastodon?
