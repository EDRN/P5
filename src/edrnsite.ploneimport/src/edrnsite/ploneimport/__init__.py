# encoding: utf-8

'''📦 EDRN Site Import from Plone.'''

import pkg_resources


PACKAGE_NAME = __name__
__version__ = VERSION = pkg_resources.resource_string(__name__, 'VERSION.txt').decode('utf-8').strip()
