# encoding: utf-8

'''🎛 EDRN Site Controls: asynchronous tasks.'''

from .models import Informatics
from celery import shared_task
from django.core.cache import cache
from urllib.request import urlopen
from wagtail.models import Site
import logging


_logger = logging.getLogger(__name__)


@shared_task
def do_update_my_ip():
    _logger.info('🔓 Getting lock for `update_my_up`')
    with cache.lock('update_my_ip', timeout=300):
        settings = Informatics.for_site(Site.objects.filter(is_default_site=True).first())
        _logger.info('🤓 Looking up my IP with %s', settings.ip_address_service)
        try:
            with urlopen(settings.ip_address_service) as io:
                my_ip = io.read().decode('utf-8')
                _logger.info('🎉 Got %s', my_ip)
        except Exception as ex:
            my_ip = str(ex)
            _logger.exception('😔 Could not get my_ip')
        settings.ip_address = my_ip
        settings.save()
