# encoding: utf-8

'''🧫 EDRN Knowledge Environment Biomarmers: index model, faceted search, and RDF ingestor.'''

from .biomarker import Biomarker, BiomarkerBodySystem, BiomarkerCollaborativeGroupName, Protocol, BodySystemStudy
from .constants import HGNC_PREDICATE_URI, ORGAN_GROUPS
from django.db.models.functions import Lower
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils.text import slugify
from django_plotly_dash import DjangoDash
from eke.knowledge.models import KnowledgeFolder
from eke.knowledge.rdf import RelativeRDFAttribute
from eke.knowledge.utils import Ingestor as BaseIngestor
from sortedcontainers import SortedList
from wagtail.models import Page
import dash_core_components as dcc
import dash_html_components as html
import rdflib, logging, typing, plotly.express, collections, pandas

_logger = logging.getLogger(__name__)
_biomarker_type_uri = 'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Biomarker'


class Ingestor(BaseIngestor):
    _biomarker_resource_uri = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Biomarker')
    _bmod_type_uri          = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#BiomarkerOrganData')
    _has_org_bags_uri       = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#hasBiomarkerOrganStudyDatas')
    _has_study_bags_uri     = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#hasBiomarkerStudyDatas')
    _hgnc_pred_uri          = rdflib.URIRef(HGNC_PREDICATE_URI)
    _member_pred_uri        = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#memberOfPanel')
    _organ_pred_uri         = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Organ')
    _panel_pred_uri         = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#IsPanel')
    _ref_study_pred_uri     = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#referencesStudy')
    _title_pred_uri         = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Title')

    def _flatten(self, 𝐋: object) -> typing.Iterator[object]:
        '''Yield a potential list of lists ``𝐋`` as flat sequence of non-list items.'''
        for i in 𝐋:
            if isinstance(i, (list, SortedList)):
                for j in self._flatten(i):
                    yield j
            else:
                yield i

    def getSlug(self, uri: rdflib.URIRef, predicates: dict) -> str:
        hgnc = str(predicates.get(self._hgnc_pred_uri, [''])[0])
        if hgnc:
            candidate = slugify(hgnc)
            results = Page.objects.filter(slug=candidate)
            return candidate if results.count() == 0 else None
        else:
            return super().getSlug(uri, predicates)
        return slugify(hgnc) if hgnc else super().getSlug(uri, predicates)

    def getTitle(self, uri: rdflib.URIRef, predicates: dict) -> str:
        titles = [str(i) for i in predicates.get(self._title_pred_uri, [])]
        if len(titles) == 0: return None
        return titles[0]

    def add_biomarker_level_protocols(self):
        '''Add protocols to biomarkers.

        The protocols are in a weird RDF bag that itself references weird wrapper objects so we
        can't use the standard RDF ingest plumbing.
        '''
        modder = RelativeRDFAttribute('protocols', scalar=False)
        for uri, predicates in self.filter_by_rdf_type(self.statements, rdflib.URIRef(_biomarker_type_uri)):
            bag_uri = predicates.get(self._has_study_bags_uri, [None])[0]
            if not bag_uri: continue
            bag = self.statements.get(bag_uri)
            if not bag: continue
            bm = Biomarker.objects.filter(identifier__exact=uri).first()
            if not bm: continue
            del bag[rdflib.RDF.type]
            values = []
            for pointless_indiretion_uri in bag.values():
                useless_wrapper = self.statements.get(pointless_indiretion_uri[0])
                if not useless_wrapper: continue
                study_uri = useless_wrapper.get(self._ref_study_pred_uri, [None])[0]
                values.append(study_uri)
            modder.modify_field(bm, values, bm._meta.get_field('protocols'), predicates)
            bm.save()

    def connect_panels(self):
        '''Connect biomarker panels to their composed biomarkers.'''

        # First, build a lookup table of panel-uri → set of member uris
        empaneled = {}
        for uri, predicates in self.filter_by_rdf_type(self.statements, rdflib.URIRef(_biomarker_type_uri)):
            panel_uri = predicates.get(self._member_pred_uri, [None])[0]
            if panel_uri:
                panel_uri = str(panel_uri)
                bms = empaneled.get(panel_uri, set())
                bms.add(uri)
                empaneled[panel_uri] = bms

        # Now find each biomarker which claims to be a panel
        for uri, predicates in self.filter_by_rdf_type(self.statements, rdflib.URIRef(_biomarker_type_uri)):
            uri = str(uri)
            if int(predicates.get(self._panel_pred_uri, ['0'])[0]) == 1:
                # If it's a biomarker that was deleted, skip it
                if uri in self.deleted_biomarkers: continue

                # Get the uris of its members
                member_uris = empaneled.get(uri)
                if not member_uris:
                    # In this case, we have a biomarker with subject ``uri`` not in the ``empaneled`` dict,
                    # which means that the biomarker has ``<ns1:IsPanel>1</ns1:IsPanel>`` but no other
                    # biomarkers have claimed membership in it. So just ignore it.
                    continue                    

                # See if the set of members has changed
                bm = Biomarker.objects.filter(identifier__exact=uri).first()
                if set(bm.members.all().values_list('identifier', flat=True)) != member_uris:
                    bm.members.set(Biomarker.objects.filter(identifier__in=member_uris), clear=True)
                    bm.save()
                    # If this was a new biomarker, we're done. If it was an updated biomarker, we're done.
                    # However, it might've been an under-the-radar biomarker that was neither new nor
                    # updated, so in this case, add it to the updated roster.
                    if uri not in self.new_biomarkers and uri not in self.updated_biomarkers:
                        self.updated_biomarkers[uri] = bm

    def add_organ_protocols(self, bbs: BiomarkerBodySystem, bm_predicates: dict):
        # For body-system-studies:
        # - the title of the object is the title of the protocol
        # - but we can make the slug of the object be the slugify'd identifier and check for its existence
        #   - and like BiomarkerBodySystem, use it if it exists and create it if not
        study_data_uris = []
        for bag in bm_predicates.get(self._has_org_bags_uri, []):
            predicates = self.statements.get(bag, dict())
            del predicates[rdflib.RDF.type]  # We know it's a ``Bag``
            study_data_uris.extend(self._flatten(predicates.values()))
        for study_data_uri in study_data_uris:
            predicates = self.statements.get(study_data_uri, dict())
            protocol_uri = str(predicates.get(self._ref_study_pred_uri, [''])[0])
            if protocol_uri:
                protocol = Protocol.objects.filter(identifier=protocol_uri).first()
                if protocol:
                    bss = bbs.body_system_studies.filter(title=protocol.title).first()
                    if not bss:
                        bss = BodySystemStudy(title=protocol.title, protocol=protocol)
                        bbs.body_system_studies.add(bss, bulk=False)
                        bss.save()
                    bbs.save()
                    self.setAttributes(bss, predicates)
                    bss.save()

    def update_organ_specifics(self):
        for uri, predicates in self.filter_by_rdf_type(self.statements, rdflib.URIRef(self._bmod_type_uri)):
            biomarker_uri = predicates.get(self._biomarker_resource_uri, [None])[0]
            if not biomarker_uri or str(biomarker_uri) in self.deleted_biomarkers: continue
            organ_name = predicates.get(self._organ_pred_uri, [None])[0]
            if not organ_name: continue
            bm = Biomarker.objects.filter(identifier__exact=biomarker_uri).first()
            if not bm: continue
            bmBodySys = bm.biomarker_body_systems.filter(title__exact=organ_name).first()
            if not bmBodySys:
                bmBodySys = BiomarkerBodySystem(title=organ_name)
                bm.biomarker_body_systems.add(bmBodySys, bulk=False)
                grp_name = ORGAN_GROUPS.get(str(organ_name))
                if grp_name:
                    grp = BiomarkerCollaborativeGroupName(value=grp_name)
                    bm.biomarker_collaborative_group_names.add(grp)
                    grp.save()
                bm.save()
            bmBodySys.biomarker_bodysystem_certifications.all().delete()
            self.setAttributes(bmBodySys, predicates)
            bmBodySys.save()
            self.add_organ_protocols(bmBodySys, predicates)

    def ingest(self):
        n, u, self.deleted_biomarkers = super().ingest()

        # Convert the new and updated biomarker sets into lookup tables
        self.new_biomarkers, self.updated_biomarkers = {}, {}
        for bm in n: self.new_biomarkers[bm.identifier] = bm
        for bm in u: self.updated_biomarkers[bm.identifier] = bm

        self.add_biomarker_level_protocols()
        self.connect_panels()
        self.update_organ_specifics()

        # Convert the possibly-modified lookup tables back into sets
        return set(self.new_biomarkers.values()), set(self.updated_biomarkers.values()), self.deleted_biomarkers


class BiomarkerIndex(KnowledgeFolder):
    template = 'eke.biomarkers/biomarker-index.html'
    subpage_types = [Biomarker]
    page_description = 'Container for biomarkers'

    def get_vocabulary(self, name) -> list:
        '''Get a "vocabulary" of known values for the field ``name`` for our contained subpage.'''
        if name == 'organ':
            return BiomarkerBodySystem.objects.values_list('title', flat=True).distinct().order_by(Lower('title'))
        elif name == 'phase':
            return range(1, 6)
        else:
            return super().get_vocabulary(name)

    def get_contents(self, request: HttpRequest) -> object:
        organs = request.GET.getlist('organ')
        if organs:
            matches = Biomarker.objects.child_of(self).live().public().filter(
                biomarker_body_systems__title__in=organs
            ).order_by(Lower('title'))
        else:
            matches = Biomarker.objects.child_of(self).live().public().order_by(Lower('title'))
        phases = request.GET.getlist('phase')
        if phases:
            matches = matches.filter(biomarker_body_systems__phase__in=phases)

        # TBD what we do with phases

        query = request.GET.get('query')
        if query: matches = matches.search(query)
        return matches

    def faceted_markup(self, request):
        pages, rows = self.get_contents(request), []
        for page in pages:
            rows.append(render_to_string('eke.biomarkers/biomarker-row.html', {'biomarker': page.specific}))
        return ''.join(rows)

    def get_context(self, request: HttpRequest, *args, **kwargs) -> dict:
        context = super().get_context(request, *args, **kwargs)
        matches = context['knowledge_objects']

        bbs = BiomarkerBodySystem.objects.filter(biomarker__in=matches).all()
        by_organs = {i: 0 for i in bbs.values_list('title', flat=True).distinct()}
        p1 = p2 = p3 = p4 = p5 = 0
        for organ in bbs.all():
            if organ.phase == 1:
                p1 += 1
                by_organs[organ.title] += 1
            elif organ.phase == 2:
                p1 += 1
                p2 += 1
                by_organs[organ.title] += 2
            elif organ.phase == 3:
                p1 += 1
                p2 += 1
                p3 += 1
                by_organs[organ.title] += 3
            elif organ.phase == 4:
                p1 += 1
                p2 += 1
                p3 += 1
                p4 += 1
                by_organs[organ.title] += 4
            elif organ.phase == 5:
                p1 += 1
                p2 += 1
                p3 += 1
                p4 += 1
                p5 += 1
                by_organs[organ.title] += 5

        context['phase_1'], context['phase_2'], context['phase_3'], context['phase_4'], context['phase_5'] = p1, p2, p3, p4, p5
        phases_frame = pandas.DataFrame({'Phase': ['1', '2', '3', '4', '5'], 'Count': [p1, p2, p3, p4, p5]})
        phases_figure = plotly.express.pie(phases_frame, values='Count', names='Phase', title='Phases')
        organs, amounts = [i[0] for i in by_organs.items()], [i[1] for i in by_organs.items()]
        organs_frame = pandas.DataFrame({'Organ': organs, 'Count': amounts})
        organs_figure = plotly.express.bar(organs_frame, x='Organ', y='Count', title='Body Systems')

        app = DjangoDash('BiomarkerDashboard')  # ← referenced in biomarker-index.html
        app.layout = html.Div(className='row', children=[
            dcc.Graph(id='body-systems', figure=organs_figure, className='col-md-8'),
            dcc.Graph(id='phases', figure=phases_figure, className='col-md-4'),
        ])
        return context

    def serve(self, request: HttpRequest) -> HttpResponse:
        '''Overridden service.

        We override serve in order to handle the ``ajax=organs`` request.
        '''
        if request.GET.get('ajax') == 'organs':
            organs = BiomarkerBodySystem.objects.distinct().values_list('title', flat=True).order_by('title')
            return JsonResponse({'data': [i for i in organs]})
        else:
            return super().serve(request)

    class Meta:
        pass
    class RDFMeta:
        ingestor = Ingestor
        types = {
            _biomarker_type_uri: Biomarker,
        }
