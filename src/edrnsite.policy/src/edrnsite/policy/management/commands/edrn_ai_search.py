# encoding: utf-8

'''🧬 EDRN Site: AI search.'''

from edrnsite.controls.models import Search
from django.core.management.base import BaseCommand, CommandError
import os


_system_prompt = 'Act as a search assistant for the Early Detection Research Network, summarizing voluminous search results into easily digestible summaries.'


class Command(BaseCommand):
    '''Set up EDRN AI search.'''

    help = 'Sets up values for AI-enhanced search'

    def handle(self, *args, **options):
        access_key, secret_key = os.getenv('BEDROCK_ACCESS_KEY'), os.getenv('BEDROCK_SECRET_KEY')
        if access_key is None or secret_key is None:
            raise CommandError('Expect both the BEDROCK_ACCESS_KEY and BEDROCK_SECRET_KEY env vars to be set')
            
        search, _ = Search.objects.get_or_create()
        search.bedrock_access_key, search.bedrock_secret_key = access_key, secret_key
        search.when_to_enable_ai = 20
        search.bedrock_region = 'us-west-2'
        search.system_prompt = _system_prompt
        search.save()
