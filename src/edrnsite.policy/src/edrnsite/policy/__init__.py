# encoding: utf-8

'''🧬 EDRN Site'''

from .celery import app as celery_app
import importlib.metadata


PACKAGE_NAME = __name__
__version__ = VERSION = importlib.metadata.version(__name__)


__all__ = (
    celery_app,
    PACKAGE_NAME,
    VERSION,
)
