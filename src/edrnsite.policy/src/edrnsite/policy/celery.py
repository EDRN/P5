# encoding: utf-8

'''🧬 EDRN Site: task queues using Celery.'''

from celery import Celery
import os


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edrnsite.policy.settings.ops')
app = Celery('EDRN')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
