# encoding: utf-8

'''😌 EDRN Site Content: Django forms.'''

from django import forms
from django.forms.utils import ErrorList
from eke.knowledge.models import Site, Person, Protocol, BodySystem

ALL_USERS_DN = 'cn=All Users,dc=edrn,dc=jpl,dc=nasa,dc=gov'


def protocol_choices():
    return [(i.identifier, f'{i.title} ({i.protocolID})') for i in Protocol.objects.all().order_by('title')]


def organ_choices():
    return [(i.identifier, i.title) for i in BodySystem.objects.all().order_by('title')]


def institution_choices():
    '''Vocabulary for choices of institution in choice fields.'''
    return [(i.identifier, f'{i.title} ({i.dmccSiteID})') for i in Site.objects.all().order_by('title')]


def pi_choices():
    '''Vocabulary for choices for principal investigators.'''
    return [
        (i.identifier, i.title)
        for i in Person.objects.filter(pk__in=Site.objects.values_list('pi', flat=True)).order_by('title')
    ]


def pi_site_choices():
    '''Vocabulary for choices for principal investigators and their sites.'''

    _kinds = {
        'Clinical Validation Center', 'Data Management and Coordinating Center', 'National Cancer Institute',
        'Biomarker Reference Laboratories', 'Associate Member A - EDRN Funded', 'Associate Member B',
        'Associate Member C', 'Biomarker Characterization Center', 'Biomarker Developmental Laboratories'
    }
    return [
        (
            f'{site.dmccSiteID}-{site.pi.personID}',
            f'{site.pi.title.strip()} ({site.title.strip()}, {site.memberType}, site ID {site.dmccSiteID})'
        ) for site in Site.objects.filter(
            memberType__in=_kinds
        ).exclude(dmccSiteID=None).exclude(pi=None).exclude(pi__personID=None).order_by('pi__title')
    ]


def discipline_choices():
    '''Vocabulary for choices for disciplines.'''
    return [
        ('genomics', 'Genomics'),
        ('proteomics', 'Proteomics'),
        ('pathology-images', 'Pathology Imagess'),
        ('radiology', 'Radiology'),
        ('immunology', 'Immunology'),
        ('pathology', 'Pathology'),
        ('undefined', 'Undefined')
    ]


def data_category_choices():
    '''Vocabulary for choices for data categories.'''
    categories = (
        'Antibody Microarray',
        'Biospecimen',
        'Clinical',
        'CT',
        'DNA Methylation Sequencing',
        'DNA Microarray Analysis',
        'Documentation',
        'ELISA',
        'Fluoroscopy',
        'Immunoassay',
        'Immunohistochemestry',
        'LabMAP',
        'Luminex',
        'Mammography',
        'Mass Spectrometry',
        'MRI',
        'Multiplex-Immunofluorescent Staining',
        'PET',
        'Protein Microarray',
        'Radiomics',
        'RNA Sequencing',
        'Sequencing',
        'Single Slide Image',
        'Tissue Micro Array',
        'Whole Slide Imaging',
        'Other (specify below)',
    )
    return [(i.lower().replace(' ', '-'), i) for i in categories]


class BootstrapErrorList(ErrorList):
    '''Custom ErrorList that uses a Bootstrap-compatible default CSS class.'''
    def __init__(self, initlist=None, error_class=None, renderer=None):
        if error_class is None:
            error_class = 'text-danger'
        super().__init__(initlist, error_class, renderer)


class AbstractEDRNForm(forms.Form):
    '''This is an abstract form that sets up our preferred styles.'''
    template_name = 'edrnsite.content/form-rendering.html'
    template_name_label = 'edrnsite.content/label-rendering.html'
    error_css_class = 'is-invalid'
    required_css_class = 'is-required'

    def __init__(
        self,
        data=None,
        files=None,
        auto_id='id_%s',
        prefix=None,
        initial=None,
        error_class=BootstrapErrorList,
        label_suffix=None,
        empty_permitted=False,
        field_order=None,
        use_required_attribute=None,
        renderer=None,
        page=None
    ):
        super().__init__(
            data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, field_order,
            use_required_attribute, renderer
        )
        self.page = page

    @staticmethod
    def get_encoding_type() -> str:
        '''Subclasses can override this if they need something other than ``application/x-www-form-urlencoded``.'''
        return 'application/x-www-form-urlencoded'

    class Meta:
        abstract = True
