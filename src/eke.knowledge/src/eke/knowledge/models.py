# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: models.'''


from .committees import CommitteeIndex
from .knowledge import KnowledgeObject, KnowledgeFolder, RDFSource
from .publications import Publication, PublicationIndex, PMCID, PublicationSubjectURI
from .bodysystems import BodySystem, BodySystemIndex
from .diseases import Disease, DiseaseIndex
from .miscresources import MiscellaneousResource, MiscellaneousResourceIndex
from .protocols import ProtocolIndex, Protocol
from .sciencedata import DataCollection, DataCollectionIndex
from .sites import Site, SiteIndex, Person, OrganizationalGroup
from django.db import models
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.admin.panels import FieldPanel


@register_setting
class RDFIngest(BaseSiteSetting):
    enabled = models.BooleanField(blank=False, null=False, default=True, help_text='Global enable/disable RDF ingest')
    timeout = models.PositiveIntegerField(
        blank=False, null=False, default=120, help_text='Max time limit for ingest in minutes; 0 disables timeout',
    )
    # Dan's D.D.:
    edrn_protocol_limit = models.IntegerField(
        blank=False, null=False, default=1000, help_text='Protocol IDs over this number are considered non-EDRN'
    )
    last_ingest_start = models.DateTimeField(blank=True, null=True, help_text='When the last ingest started')
    last_ingest_duration = models.IntegerField(blank=True, null=True, help_text='How long (seconds) last ingest took')
    panels  = [FieldPanel('enabled'), FieldPanel('timeout'), FieldPanel('edrn_protocol_limit')]
    class Meta:
        verbose_name = 'RDF Ingest'


__all__ = [
    BodySystem,
    BodySystemIndex,
    CommitteeIndex,
    DataCollection,
    DataCollectionIndex,
    Disease,
    DiseaseIndex,
    KnowledgeFolder,
    KnowledgeObject,
    MiscellaneousResource,
    MiscellaneousResourceIndex,
    OrganizationalGroup,
    Person,
    PMCID,
    Protocol,
    ProtocolIndex,
    Publication,
    PublicationIndex,
    PublicationSubjectURI,
    RDFIngest,
    RDFSource,
    Site,
    SiteIndex,
]
