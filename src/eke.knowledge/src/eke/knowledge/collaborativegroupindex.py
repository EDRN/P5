# encoding: utf-8


u'''EKE Knowledge: Collaborative Group Index'''

# from .person import IPerson
# from plone.memoize.view import memoize
# import plone.api
from . import _
from .biomarker import IBiomarker
from .dataset import IDataset
from .groupspaceindex import IGroupSpaceIndex
from .groupspaceindex import View as BaseView
from .protocol import IProtocol
from five import grok
from plone.app.vocabularies.catalog import CatalogSource
from z3c.relationfield.schema import RelationChoice, RelationList


class ICollaborativeGroupIndex(IGroupSpaceIndex):
    u'''Index page for a collaborative group folder.'''
    biomarkers = RelationList(
        title=_(u'Biomarkers'),
        description=_(u'Biomarkers being researched by this group.'),
        default=[],
        required=False,
        value_type=RelationChoice(
            title=_(u'Biomarker'),
            description=_(u'A single biomarker being researched by this group.'),
            source=CatalogSource(object_provides=IBiomarker.__identifier__)
        )
    )
    protocols = RelationList(
        title=_(u'Protocols'),
        description=_(u'Protocols and studies that are executed (and studied) by this group.'),
        default=[],
        required=False,
        value_type=RelationChoice(
            title=_(u'Protocol'),
            description=_(u'A single protocol or study being executed or studied by this group.'),
            source=CatalogSource(object_provides=IProtocol.__identifier__, project=False)
        )
    )
    projects = RelationList(
        title=_(u'Projects'),
        description=_(u'Projects pursued by this group.'),
        default=[],
        required=False,
        value_type=RelationChoice(
            title=_(u'Project'),
            description=_(u'A single project being executed or studied by this group.'),
            source=CatalogSource(object_provides=IProtocol.__identifier__, project=True)
        )
    )
    datasets = RelationList(
        title=_(u'Datasets'),
        description=_(u'Scientific data of interest to this collaborative group.'),
        default=[],
        required=False,
        value_type=RelationChoice(
            title=_(u'Dataset'),
            description=_(u'A single set of scientific data (or a single datum) of interest to this group.'),
            source=CatalogSource(object_provides=IDataset.__identifier__)
        )
    )


class View(BaseView):
    u'''View for a collaborative group index'''
    grok.context(ICollaborativeGroupIndex)
