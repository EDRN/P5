# encoding: utf-8

'''🩺 EDRN site testing: base classes.'''


import os
import unittest

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver, Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def _firefox_options() -> Options:
    options = Options()
    if os.environ.get('EDRN_E2E_HEADLESS', '1') != '0':
        options.add_argument('-headless')
    return options


class EDRNSmokeTestCase(unittest.TestCase):
    '''Smoke tests against a running server at BASE_URL.'''

    base_url: str
    selenium: WebDriver
    wait: WebDriverWait

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base_url = os.environ.get('BASE_URL', 'http://localhost:6468/').rstrip('/')
        cls.selenium = WebDriver(options=_firefox_options())
        cls.selenium.implicitly_wait(10)
        cls.wait = WebDriverWait(cls.selenium, 20)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def url(self, path: str) -> str:
        if not path.startswith('/'):
            path = f'/{path}'
        return f'{self.base_url}{path}'

    def get(self, path: str) -> None:
        self.selenium.get(self.url(path))

    def wait_for(self, condition, timeout: float = 20):
        return WebDriverWait(self.selenium, timeout).until(condition)

    def wait_for_element(self, by: By, value: str, timeout: float = 20):
        return self.wait_for(EC.presence_of_element_located((by, value)), timeout=timeout)

    def wait_for_text_in_body(self, text: str, timeout: float = 20):
        return self.wait_for(EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), text), timeout=timeout)


class EDRNLiveSiteTestCase(StaticLiveServerTestCase):
    '''Phase 2: isolated browser tests with an ephemeral Django test server.'''
     # 🔮 TODO: implement


class EDRNBasicContentTestCase(EDRNLiveSiteTestCase):
    fixtures = None


class EDRNPanel:
    def __init__(self, driver: WebDriver):
        self._driver = driver
