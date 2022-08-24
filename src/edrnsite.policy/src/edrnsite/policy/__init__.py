# encoding: utf-8

'''🧬 EDRN Site'''

from .celery import app as celery_app
import pkg_resources


PACKAGE_NAME = __name__
__version__ = VERSION = pkg_resources.resource_string(__name__, 'VERSION.txt').decode('utf-8').strip()


__all__ = (
    celery_app,
    PACKAGE_NAME,
    VERSION,
)
