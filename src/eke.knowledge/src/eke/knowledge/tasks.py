# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: asynchronous tasks.'''

from .models import RDFIngest
from .site_ingest import full_ingest
from .utils import aware_now
from celery import shared_task
from django.core.cache import cache
from django.core.management import call_command
from wagtail.core.models import Site
import logging

_logger = logging.getLogger(__name__)


@shared_task
def do_fix_tree():
    with cache.lock('fix_tree', timeout=3600):
        _logger.info('🌴 Calling management command `fixtree`')
        call_command('fixtree')
        _logger.info('🎬 `fixtree done')


@shared_task
def do_full_ingest():
    settings = RDFIngest.for_site(Site.objects.filter(is_default_site=True).first())
    with cache.lock('full_ingest', timeout=settings.timeout * 60):
        t0 = aware_now()
        settings.last_ingest_start = t0
        settings.save()
        n, u, d = full_ingest()
        delta = aware_now() - t0
        settings.last_ingest_duration = delta.total_seconds()
        settings.save()
        # We can't return set objects over JSON, which is what Celery is using with Redis, so convert
        # to lists:
        return [i.identifier for i in n], [i.identifier for i in u], list(d)

    # 🔮 What to do about lock errors?
    # from redis.exceptions import LockError
    # try:
    #     …
    # except LockError:
    #     _logger.exception('Lock error during ingest')


@shared_task
def do_reindex():
    with cache.lock('wagtail_update_index', timeout=3600):
        call_command('wagtail_update_index')


@shared_task
def do_ldap_group_sync():
    _logger.info('🔓 Getting lock for `ldap_group_sync`')
    with cache.lock('ldap_group_sync', timeout=60):
        _logger.info('📞 Calling management command `ldap_group_sync`')
        call_command('ldap_group_sync')
        _logger.info('🎬 `ldap_group_sync done')
