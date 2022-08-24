# encoding: utf-8

'''🧬 EDRN Site Policy: tests.'''

from .test_settings import SocialMediaSettingsTestCase
from .test_bloom import BloomTestCase

__all__ = [
    BloomTestCase,
    SocialMediaSettingsTestCase,
]
