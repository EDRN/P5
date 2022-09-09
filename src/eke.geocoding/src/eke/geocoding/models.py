 # encoding: utf-8

'''🗺 EDRN Knowledge Environment geocoding: models.'''

from django.db import models
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting


@register_setting
class Geocoding(BaseSiteSetting):
    access_key = models.CharField(
        blank=False, null=False, help_text='AWS Access Key', default='key', max_length=192
    )
    secret_key = models.CharField(
        blank=False, null=False, help_text='AWS Secret Access Key', default='key', max_length=192
    )
    class Meta:
        verbose_name = 'Geocoding'


class InvestigatorAddress(models.Model):
    '''A cached address of an investigator geocoded with coordinates.'''

    # The countries we're prepared to handle. Note that the DMCC-provided data on countries
    # is abysmal and so we have to map many possible meanings to "UNITED STATES". And since
    # we're using US Census data for geocoding, we can't handle any other country.
    _countries = {
        'U.S.': 'UNITED STATES',
        'U.S.A.': 'UNITED STATES',
        'U.S.A': 'UNITED STATES',
        'U': 'UNITED STATES',
        'US': 'UNITED STATES',
        'USA': 'UNITED STATES',
        'United States of America': 'UNITED STATES',
        'United States': 'UNITED STATES',
        'u.s.a.': 'UNITED STATES',
        'u': 'UNITED STATES',
        'usa': 'UNITED STATES',
    }

    address = models.CharField(
        default='742 EVERGREEN TERRACE, SPRINGFIELD, OR, 97057, UNITED STATES',
        max_length=512, blank=False, null=False, unique=True, help_text='Full street address'
    )
    lat = models.FloatField(blank=False, null=False, default=0.0, help_text='Latitude')
    lon = models.FloatField(blank=False, null=False, default=0.0, help_text='Longitude')

    @classmethod
    def normalize(cls: type, address: str, city: str, state: str, postal_code: str, country: str) -> str:
        # Check the country; if it's not found, we can't go any further
        country = cls._countries.get(country)
        if not country: return None

        # Check if the DMCC is abusing ``N/A``:
        if address.upper() == 'N/A' or city.upper() == 'N/A' or state.upper() == 'N/A': return None

        parts = []
        if address:
            parts.append(address.strip().upper())
        if city:
            parts.append(city.strip().upper())
        if state:
            parts.append(state.strip().upper())
        if postal_code:
            parts.append(postal_code.strip().upper())
        parts.append(country)

        return ', '.join(parts)

    def __str__(self) -> str:
        return f'{self.lat}, {self.lon}'
