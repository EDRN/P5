# encoding: utf-8

'''🩺 EDRN site testing: base classes.'''


from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver, Options


class EDRNLiveSiteTestCase(StaticLiveServerTestCase):
    pass


class EDRNBasicContentTestCase(EDRNLiveSiteTestCase):
    fixtures = None


class EDRNPanel:
    def __init__(self, driver: WebDriver):
        self._driver = driver
