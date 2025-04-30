# encoding: utf-8

'''😌 EDRN Site Content: add data disclaimer snippet.'''

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from edrnsite.content.models import BoilerplateSnippet


_default_data_disclaimer = '''Data and information released from the National Cancer Institute (NCI) are provided on
an "AS IS" basis, without warranty of any kind, including without limitation the warranties of merchantability, fitness
for a particular purpose and non-infringement. Availability of this data and information does not constitute scientific
publication. Data and/or information may contain errors or be incomplete. NCI and its employees make no representation
or warranty, express or implied, including without limitation any warranties of merchantability or fitness for a
particular purpose or warranties as to the identity or ownership of data or information, the quality, accuracy or
completeness of data or information, or that the use of such data or information will not infringe any patent,
intellectual property or proprietary rights of any party. NCI shall not be liable for any claim for any loss, harm,
illness or other damage or injury arising from access to or use of data or information, including without limitation
any direct, indirect, incidental, exemplary, special or consequential damages, even if advised of the possibility of
such damages. In accordance with scientific standards, appropriate acknowledgment of NCI should be made in any
publications or other disclosures concerning data or information made available by NCI.'''


class Command(BaseCommand):
    help = 'Add the data disclaimer snippet'

    def handle(self, *args, **options):
        try:
            self.stdout.write('Adding data disclaimer snippet')
            BoilerplateSnippet.objects.get_or_create(
                bp_code='data-disclaimer', text=_default_data_disclaimer
            )
        except IntegrityError:
            pass
