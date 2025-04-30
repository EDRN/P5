# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: audit log models.'''

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.db.models.expressions import Subquery
from django.utils.functional import cached_property
from wagtail.models import Page
from wagtail.models.audit_log import BaseLogEntry, BaseLogEntryManager, LogEntryQuerySet
from django.contrib.auth import get_user_model


class KnowledgeObjectLogEntryQuerySet(LogEntryQuerySet):
    def get_actions(self):
        return set()

    def get_user_ids(self):
        return set()

    def get_users(self):
        return get_user_model().objects.none()

    def get_content_type_ids(self):
        return set()

    def filter_on_content_type(self, content_type):
        return self.none()


class KnowledgeObjectLogEntryManager(BaseLogEntryManager):
    def get_queryset(self):
        return KnowledgeObjectLogEntryQuerySet(self.model, using=self._db)

    def get_instance_title(self, instance):
        return instance.specific_deferred.get_admin_display_title()

    def log_action(self, instance, action, **kwargs):
        return None  # 🔮 TODO: this correct?

    def viewable_by_user(self, user):
        return KnowledgeObjectLogEntry.objects.none()


class KnowledgeObjectLogEntry(BaseLogEntry):
    page = models.ForeignKey(
        "ekeknowledge.KnowledgeObject",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        related_name="+",
    )

    objects = KnowledgeObjectLogEntryManager()

    class Meta:
        ordering = ["-timestamp", "-id"]
        verbose_name = "knowledge object log entry"
        verbose_name_plural = "knowledge object log entries"

    def __str__(self):
        return "KnowledgeObjectLogEntry %d: '%s' on '%s' with id %s" % (
            self.pk,
            self.action,
            self.object_verbose_name(),
            self.page_id,
        )

    @cached_property
    def object_id(self):
        return self.page_id

    @cached_property
    def message(self):
        # for page log entries, the 'edit' action should show as 'Draft saved'
        if self.action == "wagtail.edit":
            return "Draft saved"
        else:
            return super().message
