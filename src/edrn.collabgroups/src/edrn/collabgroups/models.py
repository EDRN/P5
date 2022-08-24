# encoding: utf-8

'''👥 EDRN Collaborative Groups: models.'''

from django.db import models
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel


@register_snippet
class CollaborativeGroupSnippet(models.Model):
    '''A collaborative group.'''
    cg_code = models.CharField(max_length=10, blank=False, null=False, unique=True)
    name = models.CharField(max_length=80, blank=False, null=False, unique=True)
    panels = [FieldPanel('cg_code'), FieldPanel('name')]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Collaborative Group Snippet'
        verbose_name_plural = 'Collaborative Group Snippets'
