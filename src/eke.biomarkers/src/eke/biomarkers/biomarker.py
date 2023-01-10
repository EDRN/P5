# encoding: utf-8

'''🧫 EDRN Knowledge Environment Biomarkers: biomarker and related classes.'''

from .constants import DepictableSections as ds
from .utils import qualify_biomarker_predicate as qbp
from django.db import models
from django.db.models.functions import Lower
from django.http import HttpRequest
from eke.knowledge.models import KnowledgeObject, Protocol, Publication, MiscellaneousResource, DataCollection
from eke.knowledge.rdf import RDFAttribute, RelativeRDFAttribute
from modelcluster.fields import ParentalKey
from modelcluster.fields import ParentalManyToManyField
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.models import Page, Orderable
from wagtail.search import index


class QualityAssuredObject(models.Model):
    '''An abstract object that undergoes a quality assurance process.'''
    qa_state = models.CharField(max_length=12, blank=True, null=False, help_text='Accepted, curated, under review,…')
    content_panels = [FieldPanel('qa_state')]
    class Meta:
        abstract = True
    class RDFMeta:
        fields = {qbp('QAState'): RDFAttribute('qa_state', scalar=True)}


class PhasedObject(models.Model):
    '''An abstract object that undergoes phase changes and tracks its current phase.'''
    phase = models.PositiveIntegerField(blank=True, null=True, help_text='Current Phase (1…5)')
    content_panels = [FieldPanel('phase')]
    class Meta:
        abstract = True
    class RDFMeta:
        fields = {qbp('Phase'): RDFAttribute('phase', scalar=True)}


class ResearchedObject(models.Model):
    '''An abstract object that undergoes the standard phases of biomarker research.'''
    publications = ParentalManyToManyField(
        Publication, blank=True, verbose_name='Publications About this Biomarker',
        related_name='%(app_label)s_%(class)s_in_print'
    )
    @property
    def sorted_publications(self):
        return self.publications.order_by('title')
    resources = ParentalManyToManyField(
        MiscellaneousResource, blank=True, verbose_name='Resource Useful for this Biomarker',
        related_name='%(app_label)s_%(class)s_using_resources'
    )
    @property
    def sorted_resources(self):
        return self.resources.order_by('title')
    science_data = ParentalManyToManyField(
        DataCollection, blank=True, verbose_name='Scientific Data About this Biomarker',
        related_name='%(app_label)s_%(class)s_observed'
    )
    @property
    def sorted_science_data(self):
        return self.science_data.order_by('title')
    content_panels = [
        FieldPanel('publications'), FieldPanel('resources'), FieldPanel('science_data')
    ]
    class Meta:
        abstract = True
    class RDFMeta:
        fields = {
            qbp('referencedInPublication'): RelativeRDFAttribute('publications', scalar=False),
            qbp('referencesResource'): RelativeRDFAttribute('resources', scalar=False),
            qbp('AssociatedDataset'): RelativeRDFAttribute('science_data', scalar=False),
        }


class Biomarker(KnowledgeObject, QualityAssuredObject, ResearchedObject):
    # Plone did this one thing actually better:
    #
    #                Biomarker ←──────────────┐
    #                   △                     │
    #                   │                     │
    #          ┌────────┴───────────┐         │
    #          │                    │         │
    # ElementalBiomarker     BiomarkerPanel ◆─┘
    #
    # This is, of course, the "composite design pattern". However, with Django, foreign key fields in
    # the base class get conflicting accessors in the concrete subclasses. So for just this one case
    # we're "compressing" elemental biomarkers and biomarker panels into a single concrete ``Biomarker``
    # class and if the cardinality of the members is > 0, then it's a panel.
    #
    # Update: apparently it's possible to use string substitution in the ``related_name``; trying that
    # for ``BiomarkerBodySystem`` but sticking with singly, non-specialzied ``Biomarker`` for now.

    page_description = 'Indicator for disease'
    parent_page_types = ['ekebiomarkers.BiomarkerIndex']
    subpage_types = []
    template = 'eke.biomarkers/biomarker.html'
    hgnc_name = models.CharField(max_length=50, blank=True, null=False, help_text='HUGO Gene Nomenclature Committee name')
    biomarker_type = models.CharField(max_length=20, blank=True, null=False, help_text='Gene, protein, epigenetic, …')
    protocols = ParentalManyToManyField(
        Protocol, blank=True, verbose_name='Protocols Studying this Biomarker',
        related_name='biomarkers_researched'
    )
    @property
    def sorted_protocols(self):
        return self.protocols.order_by('title')
    members = ParentalManyToManyField('self', blank=True, verbose_name='Panel Members')
    content_panels = KnowledgeObject.content_panels + QualityAssuredObject.content_panels + ResearchedObject.content_panels + [
        FieldPanel('protocols'),
        FieldPanel('hgnc_name'),
        FieldPanel('biomarker_type'),
        FieldPanel('members'),
        InlinePanel('biomarker_aliases', label='BM Aliases'),
        InlinePanel('biomarker_access_groups', label='Access Groups'),
    ]
    search_fields = KnowledgeObject.search_fields + [
        index.SearchField('hgnc_name', boost=4),
        index.RelatedFields('biomarker_aliases', [index.SearchField('value', boost=3)])
    ]
    search_fields[0].boost = 5
    def get_context(self, request: HttpRequest, *args, **kwargs) -> dict:
        context = super().get_context(request, *args, **kwargs)

        # Figure out what parts of the biomarker should be shown. First, the basics are always there.
        visible_sections = set((ds.BASICS,))

        # Then for "Accepted" biomarkers, the rest of the sections are fine too.
        if self.qa_state == 'Accepted':
            visible_sections |= {
                ds.ORGANS, ds.STUDIES, ds.PUBLICATIONS, ds.RESOURCES, ds.SUPPLEMENTAL, ds.DATA_COL
            }
        else:
            # Now, if it's a "Curated" biomarker, a few additional sections are okay.
            if self.qa_state == 'Curated':
                visible_sections |= {ds.ORGANS, ds.PUBLICATIONS, ds.RESOURCES}

            # And if we get here, it's "Curated", "Under Review", or otherwise private. So we only add
            # sections if the logged-in user happens to be in the biomarker's matching groups.
            try:
                user_groups = frozenset(request.user.ldap_user.group_names)
                my_groups = frozenset(self.biomarker_access_groups.values_list('value', flat=True).distinct())
                if len(user_groups & my_groups) > 0 or request.user.is_staff or request.user.is_superuser:
                    # The bouncer says you're fine, so you get every section
                    visible_sections |= {
                        ds.ORGANS, ds.PUBLICATIONS, ds.RESOURCES, ds.STUDIES, ds.SUPPLEMENTAL, ds.DATA_COL
                    }
            except AttributeError:
                # Not an LDAP user, but could be staff or even the super user?
                if request.user.is_staff or request.user.is_superuser:
                    visible_sections |= {
                        ds.ORGANS, ds.PUBLICATIONS, ds.RESOURCES, ds.STUDIES, ds.SUPPLEMENTAL, ds.DATA_COL
                    }

        context['visible_sections'] = visible_sections
        return context

    def data_table(self) -> dict:
        '''Return the JSON-compatible dictionary describing this biomarker.'''
        attrs = super().data_table()
        attrs['kind'] = self.biomarker_type

        organs = self.biomarker_body_systems.values_list('title', flat=True).distinct().order_by(Lower('title'))
        attrs['organs'] = ', '.join([str(i) for i in organs])

        phases, fallback = set(), set()
        for bbs in self.biomarker_body_systems.all():
            phase = bbs.phase
            if phase is not None:
                fallback.add(phase)
            for bss in bbs.body_system_studies.all():
                phase = bss.phase
                if phase is not None:
                    phases.add(bss.phase)
        phases = phases if phases else fallback
        attrs['phases'] = ', '.join([str(i) for i in sorted(list(phases))])

        return attrs

    class RDFMeta:
        fields = {
            qbp('HgncName'): RDFAttribute('hgnc_name', scalar=True),
            qbp('Type'): RDFAttribute('biomarker_type', scalar=True),
            qbp('Alias'): RDFAttribute('biomarker_aliases', scalar=False),
            qbp('AccessGrantedTo'): RDFAttribute('biomarker_access_groups', scalar=False),
            qbp('Description'): RDFAttribute('description', scalar=True),
            **KnowledgeObject.RDFMeta.fields,
            **QualityAssuredObject.RDFMeta.fields,
            **ResearchedObject.RDFMeta.fields,
        }


class BiomarkerAlias(Orderable):
    '''Another name for a biomarker.'''
    value = models.CharField(max_length=255, blank=False, null=False, default='Alias', help_text='Alternative name')
    page = ParentalKey(Biomarker, on_delete=models.CASCADE, related_name='biomarker_aliases')
    panels = [FieldPanel('value')]
    def __str__(self): return self.value  # noqa: E704


class BiomarkerCollaborativeGroupName(Orderable):
    '''Name(s) of the collaborative group(s) which is (are) researching a biomarker.'''
    value = models.CharField(max_length=80, blank=False, null=False, default='Group', help_text='Collaborative group')
    page = ParentalKey(Biomarker, on_delete=models.CASCADE, related_name='biomarker_collaborative_group_names')
    panels = [FieldPanel('value')]
    def __str__(self): return self.value  # noqa: E704


class BiomarkerAccessGroup(Orderable):
    '''What groups may have full access to a biomarker.'''
    value = models.CharField(
        max_length=255, blank=False, null=False, default='Group Name', help_text='Name (only) of group (not a full DN)'
    )
    page = ParentalKey(Biomarker, on_delete=models.CASCADE, related_name='biomarker_access_groups')
    panels = [FieldPanel('value')]
    def __str__(self): return self.value  # noqa: E704


class BiomarkerBodySystem(ResearchedObject, PhasedObject, QualityAssuredObject, models.Model):
    '''Research into a biomarker's effects on a single organ.'''
    title = models.CharField(max_length=30, blank=False, null=False, help_text='Organ Name')
    biomarker = models.ForeignKey(
        Biomarker, on_delete=models.CASCADE, related_name='biomarker_body_systems'
    )
    description = models.TextField(blank=True, null=False, help_text='A short summary')
    performance_comment = models.TextField(blank=True, null=False, help_text='How well this biomarker is doing')
    content_panels = Page.content_panels + ResearchedObject.content_panels + PhasedObject.content_panels + QualityAssuredObject.content_panels + [
        FieldPanel('performance_comment'), InlinePanel('biomarker_bodysystem_certifications')
    ]
    @property
    def sorted_studies(self):
        return self.body_system_studies.all().order_by('title')
    def __str__(self):
        return self.title
    class RDFMeta:
        fields = {
            qbp('Description'): RDFAttribute('description', scalar=True),
            qbp('PerformanceComment'): RDFAttribute('performance_comment', scalar=True),
            qbp('certification'): RDFAttribute('biomarker_bodysystem_certifications', scalar=False),
            **ResearchedObject.RDFMeta.fields,
            **PhasedObject.RDFMeta.fields,
            **QualityAssuredObject.RDFMeta.fields,
        }


class BiomarkerBodySystemCertification(models.Model):
    value = models.URLField(blank=False, null=False, default='https://some/cert', help_text='Certification URL')
    bbs = models.ForeignKey(
        BiomarkerBodySystem, on_delete=models.CASCADE, related_name='biomarker_bodysystem_certifications'
    )
    panels = [FieldPanel('value')]
    def __str__(self): return self.value  # noqa: E704


class BodySystemStudy(ResearchedObject, PhasedObject, models.Model):
    '''Protocol-specific information on a biomarker's effects on a single organ.

    In Plone we modeled this as a page. Why are we doing this here?
    '''
    title = models.CharField(max_length=250, blank=False, null=False, help_text='Protocol Title')
    bbs = models.ForeignKey(
        BiomarkerBodySystem, on_delete=models.CASCADE, related_name='body_system_studies'
    )
    protocol = models.ForeignKey(
        Protocol, null=True, blank=True, verbose_name='The Main Protocol Researching this Organ on this Biomarker',
        related_name='organs_on_biomarkers', on_delete=models.SET_NULL
    )
    decision_rule = models.CharField(max_length=80, null=False, blank=True, verbose_name='Decision rule is …')
    content_panels = Page.content_panels + [
        FieldPanel('protocol'),
        FieldPanel('decision_rule'),
    ] + ResearchedObject.content_panels + PhasedObject.content_panels
    class RDFMeta:
        fields = {
            qbp('DecisionRule'): RDFAttribute('decision_rule', scalar=True),
            **ResearchedObject.RDFMeta.fields,
            **PhasedObject.RDFMeta.fields,
        }
