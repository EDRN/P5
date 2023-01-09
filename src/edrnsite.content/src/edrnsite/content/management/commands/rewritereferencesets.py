# encoding: utf-8

'''😌 EDRN Site Content: rewrite refence sets page.'''

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.cache import caches
from django.core.management.base import BaseCommand
from django.db.models.functions import Lower
from edrn.collabgroups.models import Committee
from edrnsite.content.models import FlexPage
from edrnsite.ploneimport.classes import PaperlessExport, PlonePage
from edrnsite.policy.management.commands.utils import set_site
from eke.knowledge.models import CommitteeIndex, RDFSource, SiteIndex
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.models import Page, PageViewRestriction
from wagtail.rich_text import RichText
import argparse, pkg_resources
from wagtail.contrib.typed_table_block.blocks import TypedTable
from wagtail.blocks.field_block import CharBlock
from edrnsite.streams.blocks import TYPED_TABLE_BLOCK


class Command(BaseCommand):
    help = 'Rewrite the Specimens Reference Sets pages'

    def create_folder(self, parent: Page, title: str) -> Page:
        '''Create a "folder" with the given ``title`` as a child of ``parent``, deleting it if it already
        exists. Return the newly created folder.
        '''
        folder = parent.get_children().filter(title=title).first()
        if folder is not None:
            folder.delete()
            parent.refresh_from_db()
        folder = FlexPage(title=title, live=True)
        parent.add_child(instance=folder)
        folder.save()
        return folder

    def create_groups_container(self, parent: Page) -> Page:
        index = parent.get_children().filter(slug='groups').first()
        if index is not None:
            index.delete()
            parent.refresh_from_db()
        index = CommitteeIndex(
            title='Committees and Collaborative Groups', slug='groups', live=True, show_in_menus=False,
            ingest_order=90, seo_title='Committees', draft_title='Groups'
        )
        index.rdf_sources.add(RDFSource(name='DMCC Committees', url=_committees_url, active=True))
        parent.add_child(instance=index)
        index.save()
        return index

    def create_network_consulting_team(self, home_page: Page, source: PlonePage):
        home_page.get_children().filter(title='Network Consulting Team').delete()
        home_page.refresh_from_db()
        nct_page = source.install(home_page)
        source.rewrite_html()

        overview = nct_page.get_children().filter(title='Overview').first().specific
        del overview.body[0]
        overview.body.append(('rich_text',
            RichText(pkg_resources.resource_string(__name__, 'data/overview.html').decode('utf-8').strip())
        ))
        overview.save()

        objectives = nct_page.get_children().filter(title='Objectives and Responsibilities').first().specific
        del objectives.body[0]
        objectives.body.append(('rich_text',
            RichText(pkg_resources.resource_string(__name__, 'data/objectives.html').decode('utf-8').strip())
        ))
        objectives.save()

        weird_page = Page.objects.filter(title='NCT 2020: New Docs NCT 2020 AVAILABLE').first()
        nct_group = Page.objects.filter(title='Committees and Collaborative Groups').first().get_descendants().filter(title='Network Consulting Team').first()
        pks = {
            'nct_2020_new_docs_nct_2020_available': weird_page.pk,
            'network_consulting_team': nct_group.pk,
            'accomplishments': Document.objects.filter(title='EDRN Accomplishments November 2013').first().pk,
            'amp': Document.objects.filter(title='EDRN Associate Membership Program').first().pk,
            'pm': Document.objects.filter(title='EDRN Performance Metrics').first().pk,
            'h': Document.objects.filter(title='EDRN Scientific Research Highlights November 2013 (Updated)').first().pk,
            'sp': Document.objects.filter(title='EDRN Strategic Plan 2013 (Update 1)').first().pk,
            'overview': overview.pk,
            'objectives': objectives.pk,
            'past': nct_page.get_children().filter(slug='meetings').first().pk,
            'reports': nct_page.get_children().filter(slug='program-reports').first().pk
        }
        body = pkg_resources.resource_string(__name__, 'data/nct.html').decode('utf-8').strip()
        del nct_page.body[0]
        nct_page.body.append(('rich_text', RichText(body.format(**pks))))
        nct_page.show_in_menus = False
        nct_page.save()

        PageViewRestriction.objects.filter(page=nct_page).delete()
        pvr = PageViewRestriction(page=nct_page, restriction_type='groups')
        pvr.save()
        pvr.groups.set(Group.objects.filter(name__in=NCT_GROUP_ACCESS), clear=True)

        return nct_page

    def create_groups(self, site, home_page: Page, mission_and_structure: Page, source: PlonePage):
        '''Create the new groups container.'''
        plone_committees = {i.item_id: i for i in source.children}

        groups = mission_and_structure.get_children().filter(slug='groups').first()
        assert groups is not None
        groups.get_children().exclude(slug='steering-committee').delete()
        current_steering_committee = groups.get_children().filter(slug='steering-committee').first()
        assert current_steering_committee is not None
        current_steering_committee.move(home_page, pos='last-child')
        current_steering_committee.refresh_from_db()
        groups.refresh_from_db()
        home_page.refresh_from_db()
        mission_and_structure.get_children().filter(slug='groups').delete()
        mission_and_structure.refresh_from_db()
        groups = self.create_groups_container(mission_and_structure)
        for key, attributes in _groups.items():
            id_number, ldap_group, description = attributes
            if key in plone_committees:
                # Old commitee from Plone
                committee = Committee(
                    title=plone_committees[key].title, slug=key, live=True, id_number=id_number,
                    description=description
                )
                groups.add_child(instance=committee)
                committee.save()

                if key.endswith('cancers-research-group'):
                    archive = self.create_folder(committee, 'Archived Documents')
                else:
                    archive = committee
                for doc in [i for i in plone_committees[key].children if i is not None]:
                    doc.install(archive)
                    doc.rewrite_html()
                if key.endswith('cancers-research-group'):
                    self.write_index(archive, '<p>The following documents are archived in this folder:</p>')

            else:
                # New commitee
                committee = Committee(
                    title=' '.join([i.title() for i in key.split('-')]), slug=key, live=True, id_number=id_number,
                    description=description
                )
                groups.add_child(instance=committee)
                committee.save()

            if key == 'network-consulting-team':
                pvr = PageViewRestriction(page=committee, restriction_type='groups')
                pvr.save()
                pvr.groups.set(Group.objects.filter(name__in=NCT_GROUP_ACCESS), clear=True)
            elif ldap_group:
                pvr = PageViewRestriction(page=committee, restriction_type='groups')
                pvr.save()
                pvr.groups.set(Group.objects.filter(name=ldap_group), clear=True)

        new_steering_committee = Committee(
            title='Steering Committee', slug='steering-committee', live=True, id_number='1',
            description='''The Steering Committee (SC) has major scientific management oversight and responsibility for developing and implementing a collaborative Network research program including protocols, publications, and design. The Committee consists of a Chair, Co-chair, the EDRN Principal Investigators or a designee, and the NCI Program Coordinator or a designee. Members of the SC review all data collected in Network studies, monitor study results, follow-up, and report to the full SC upon request of the Chair. Each member has one vote.'''
        )
        groups.add_child(instance=new_steering_committee)
        pvr = PageViewRestriction(page=new_steering_committee, restriction_type='groups')
        pvr.save()
        pvr.groups.set(Group.objects.filter(name='Steering Committee'), clear=True)
        new_steering_committee.save()
        for page in current_steering_committee.get_children():
            page.move(new_steering_committee, pos='last-child')
        site.root_page.get_children().filter(slug='steering-committee').delete()

    def move_rdf_sites(self, site, home_page):
        FlexPage.objects.filter(slug='sites').delete()
        sites = SiteIndex.objects.filter(slug='sites-rdf').first()
        assert sites is not None
        sites.title, sites.slug = 'Sites', 'sites'
        sites.save()

    def rewrite_mission_and_structure(self, site, home_page):
        mas = FlexPage.objects.filter(slug='mission-and-structure').first()
        assert mas is not None
        del mas.body[0]
        body = pkg_resources.resource_string(__name__, 'data/mas.html').decode('utf-8').strip()
        groups = mas.get_children().filter(slug='groups').first()
        assert groups is not None
        pks = {
            'org_chart': Image.objects.filter(title='New Organization Chart').first().pk,
            'sites': SiteIndex.objects.first().pk,
            'groups': groups.pk,
            'sc': groups.get_children().filter(title='Steering Committee').first().pk,
        }
        mas.body.append(('rich_text', RichText(body.format(**pks))))
        mas.save()

    def _clean_slate(self, ref_sets: FlexPage):
        while True:
            try:
                ref_sets.body.pop()
            except IndexError:
                break

    def _create_ovarian_breast_page(self, ref_sets: FlexPage) -> int:
        desc = Document.objects.filter(file='documents/BRSCW_final1_2-6-07LF.pdf').first()
        assert desc is not None
        app = Document.objects.filter(file='documents/EDRN_BRSCW_Reference_Set_Application_Form_04_02_2015.pdf').first()
        assert app is not None
        ref_sets.get_children().filter(title='Ovarian & Breast Cancer Reference Sets').delete()
        page = FlexPage(title='Ovarian & Breast Cancer Reference Sets', live=True, show_in_menus=False)
        ref_sets.add_child(instance=page)
        page.body.append(('rich_text', RichText(f'''<p><a id="{desc.pk}" linktype="document">Biomarker Reference Sets for
                Cancers in Women (BRSCW)</a> (PDF)<br/>
                Description of pooled reference sets for ovarian and breast cancer serum specimens
                </p>
                <p><a id="{app.pk}" linktype="document">BRSCW Application Form</p>
        ''')))
        page.save()
        return page.pk

    def _create_breast_page(self, ref_sets: FlexPage) -> int:
        summary = Document.objects.filter(file='documents/breast_refset_summary.pdf').first()
        assert summary is not None
        prot = Document.objects.filter(file='documents/breastrefset-protocol-v1.1.pdf').first()
        assert prot is not None
        forms = Document.objects.filter(file='documents/breast_reference_set_forms.pdf').first()
        assert forms is not None
        app = Document.objects.filter(file='documents/EDRN_General_Reference_Set_Application_Form_04_02_2015.docx').first()
        assert app is not None
        ref_sets.get_children().filter(title='Breast Cancer Reference Sets').delete()
        page = FlexPage(title='Breast Cancer Reference Sets', live=True, show_in_menus=False)
        ref_sets.add_child(instance=page)
        page.body.append(('rich_text', RichText(f'''
            <p><a id="{summary.pk}" linktype="document">Breast Reference Set Summary</a> (PDF)</p>
            <p><a id="{prot.pk}" linktype="document">Breast Reference Set Protocol</a> (PDF)</p>
            <p><a id="{forms.pk}" linktype="document">Breast Reference Set Participant and Clinical Forms</a> (PDF)</p>
            <p><a id="{app.pk}" linktype="document">Application Form for EDRN Reference Sets</a> (PDF)</p>
        ''')))
        page.save()
        return page.pk

    def _create_bbd_page(self, ref_sets: FlexPage) -> int:
        summary = Document.objects.filter(file='documents/BBD_Refset_summary_document_2018-06-27.pdf').first()
        assert summary is not None
        app = Document.objects.filter(file='documents/Benign_Breast_Disease_Application_04_02_2015.pdf').first()
        assert app is not None
        sop = Document.objects.filter(file='documents/final_bbd_protocol_for_validation_5-7-2014.pdf').first()
        assert sop is not None
        ref_sets.get_children().filter(title='Benign Breast Disease Tissue Resource (BBD)').delete()
        page = FlexPage(title='Benign Breast Disease Tissue Resource (BBD)', live=True, show_in_menus=False)
        ref_sets.add_child(instance=page)
        page.body.append(('rich_text', RichText(f'''
            <p><a id="{summary.pk}" linktype="document">BBD Reference Set Summary Document</a> (PDF)</p>
            <p><a id="{app.pk}" linktype="document">Benign Breast Disease Application</a> (PDF)</p>
            <p><a id="{sop.pk}" linktype="document">SOP For Selection of Benign Breast Disease Project</a> (PDF)</p>
        ''')))
        page.save()
        return page.pk

    def _create_lung_page(self, ref_sets: FlexPage) -> int:
        doc = Document.objects.filter(file='documents/lcbg_protocol_apr_14_2010.pdf').first()
        assert doc is not None
        app = Document.objects.filter(file='documents/EDRN_General_Reference_Set_Application_Form_04_02_2015.docx').first()
        assert app is not None
        ref_sets.get_children().filter(title='Lung Cancer Reference Sets').delete()
        page = FlexPage(title='Lung Cancer Reference Sets', live=True, show_in_menus=False)
        ref_sets.add_child(instance=page)
        page.body.append(('rich_text', RichText(f'''
            <p><a id="{doc.pk}" linktype="document">Lung Cancer Reference Set Documentation</a> (PDF)<br/>
            The goal of the NCI/EDRN/SPORE Lung Cancer Biomarkers Group (LCBG) is to develop the requisite sample
            resources to pre-validate serum/plasma biomarkers for the early diagnosis of lung cancer.
            </p>
            <p><a id="{app.pk}" linktype="document">Application Form for EDRN Reference Sets</a> (PDF)</p>
        ''')))
        page.save()
        return page.pk

    def _create_colon_page(self, ref_sets: FlexPage) -> int:
        doc = Document.objects.filter(file='documents/EDRN_colon_reference_set.pdf').first()
        assert doc is not None
        app = Document.objects.filter(file='documents/EDRN_General_Reference_Set_Application_Form_04_02_2015.docx').first()
        assert app is not None
        ref_sets.get_children().filter(title='Colon Cancer Reference Sets').delete()
        page = FlexPage(title='Colon Cancer Reference Sets', live=True, show_in_menus=False)
        ref_sets.add_child(instance=page)
        page.body.append(('rich_text', RichText(f'''
            <p><a id="{doc.pk}" linktype="document">Colon Cancer Reference Set Documentation</a> (PDF)</p>
            <p><a id="{app.pk}" linktype="document">Application Form for EDRN Reference Sets</a> (PDF)</p>
        ''')))
        page.save()
        return page.pk

    def _create_prostate_page(self, ref_sets: FlexPage) -> int:
        doc = Document.objects.filter(file='documents/Prostate_Ref_SOP.pdf').first()
        assert doc is not None
        app = Document.objects.filter(file='documents/EDRN_General_Reference_Set_Application_Form_04_02_2015.docx').first()
        assert app is not None
        pca3 = Document.objects.filter(file='documents/pca3_protocol_v2.0_clean.pdf').first()
        assert pca3 is not None
        ref_sets.get_children().filter(title='Protstate Reference Sets').delete()
        page = FlexPage(title='Protstate Reference Sets', live=True, show_in_menus=False)
        ref_sets.add_child(instance=page)
        page.body.append(('rich_text', RichText(f'''
            <p><a id="{doc.pk}" linktype="document">Protstate Reference Set Documentation</a> (PDF)<br/>
                One of the goals of the EDRN Genitourinary (GU) Collaborative Group is the establishment of a biologic
                sample set on men prior to prostate biopsy, in association with clinical information and common data elements appropriate for evaluation of risk and prognosis of prostate cancer.
            </p>
            <p><a id="{app.pk}" linktype="document">Application Form for EDRN Reference Sets</a> (PDF)</p>
            <h3>PCA3 Validation Study and Urinary Reference Set</h3>
            <p><a id="{pca3.pk}" linktype="document">PCA3 Validation Trial and Urinary Reference Set Protocol</a>
                (PDF)
            </p>
        ''')))
        page.save()
        return page.pk

    def _create_liver_page(self, ref_sets: FlexPage) -> int:
        doc = Document.objects.filter(file='documents/EDRN_HCC_Reference_Set.pdf').first()
        assert doc is not None
        app = Document.objects.filter(file='documents/EDRN_General_Reference_Set_Application_Form_04_02_2015.docx').first()
        assert app is not None
        ref_sets.get_children().filter(title='Liver (Hepatocellular Carcinoma) Reference Set').delete()
        page = FlexPage(title='Liver (Hepatocellular Carcinoma) Reference Set', live=True, show_in_menus=False)
        ref_sets.add_child(instance=page)
        page.body.append(('rich_text', RichText(f'''
            <p><a id="{doc.pk}" linktype="document">Hepatocellular Carcinoma Reference Set Description</a> (PDF)</p>
            <p><a id="{app.pk}" linktype="document">Application Form for EDRN Reference Sets</a> (PDF)</p>
        ''')))
        page.save()
        return page.pk

    def _create_pancreas_page(self, ref_sets: FlexPage) -> int:
        doc = Document.objects.filter(file='documents/EDRN_Pancreatic_Cancer_Reference_Set_Access_Information.pdf').first()
        assert doc is not None
        app = Document.objects.filter(file='documents/EDRN_General_Reference_Set_Application_Form_04_02_2015.docx').first()
        assert app is not None
        ref_sets.get_children().filter(title='Pancreatic Standard Specimen Reference Set').delete()
        page = FlexPage(title='Pancreatic Standard Specimen Reference Set', live=True, show_in_menus=False)
        ref_sets.add_child(instance=page)
        page.body.append(('rich_text', RichText(f'''
            <p><a id="{doc.pk}" linktype="document">Pancreatic Cancer Reference Set Access Information</a> (PDF)</p>
            <p><a id="{app.pk}" linktype="document">Application Form for EDRN Reference Sets</a> (PDF)</p>
        ''')))
        page.save()
        return page.pk

    def _add_general_documents(self, ref_sets: FlexPage):
        guidelines = Page.objects.filter(slug='edrn-prevalidation-reference-set-specimen-sharing-guidelines').first()
        assert guidelines is not None
        application = Document.objects.filter(title='EDRN General Reference Set Application').first()
        assert application is not None
        ref_sets.body.append(('rich_text', RichText(f'''<h2>General Documents for Reference Sets</h2>
            <p><a id="{guidelines.pk}" linkttype="page">EDRN Guidelines</a><br/>
                <a id="{application.pk}" linktype="document">Application Form for EDRN Reference Sets</>
        ''')))

    def _add_table(self, ref_sets: FlexPage, brscw, breast, bbd, lung, colon, prostate, liver, pancreas):
        # Possible types are text, rich_text, numeric, integer, page
        columns = [
            {'type': 'text', 'heading': 'Organ'},
            {'type': 'text', 'heading': 'Protocol ID'},
            {'type': 'rich_text', 'heading': 'Reference set title'},
            {'type': 'text', 'heading': 'Cases'},
            {'type': 'text', 'heading': 'Controls'},
            {'type': 'text', 'heading': 'Total participants'},
            {'type': 'text', 'heading': 'Participants groups'},
            {'type': 'text', 'heading': 'Specimen type'},
            {'type': 'text', 'heading': 'Number of specimens'},
            {'type': 'text', 'heading': 'Volume range (mL)'},
            {'type': 'text', 'heading': 'Specimens at NCI-F?'},
            {'type': 'text', 'heading': 'Sequential samples?'},
            {'type': 'text', 'heading': 'Follow-up data?'},
            {'type': 'text', 'heading': 'Pathology'},
            {'type': 'text', 'heading': 'Image files avail?'},
            {'type': 'text', 'heading': 'Incidental cancer?'},
        ]
        bbd = [
            'Breast', '331', f'<a id="{bbd}" linktype="page">Benign Breast Disease</a>',
            '30', '62', '92', 'BBD that progressed to cancer BBD controls', 'Tissue slides',
            '9,256', '"each"', 'No, at Kansas', 'N/A', 'No', 'Yes', 'No', 'Yes'
        ]
        breast1 = [
            'Breast', '121', f'<a id="{breast}" linktype="page">Breast</a>',
            '262', '570', '832', 'Pre-diagnosis specimens, DCIS cases, Invasive cancer cases, LCIS cases, Benign→later cancer cases, Normal→later cancer cases, Benign Disease Atypia controls, Benign Disease non-Atypia controls, Normal controls',
            'Serum', '16,444', '0.01–0.8', 'Yes', 'No', 'No', 'Yes', 'No', 'Yes'
        ]
        breast2 = [
            '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Plasma', '16,169', '0.01–0.9', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠'
        ]
        ovarian = [
            'Ovarian & Breast', 118, f'<a id="{brscw}" linktype="page">Cancers in women-BRSCW</a>',
            '441', '95', '536', 'Cases (pooled), controls (pooled)', 'Serum', '105 sets', '0.3',
            'Yes', 'No', 'No', 'No', 'No', 'No'
        ]
        colon1 = [
            'Colon', '251', f'<a id="{colon}" linktype="page">Colon cancer</a>', '50', '100', '150', '⁠', 'Serum',
            '2,100', '0.3', 'Yes', 'No', 'No', 'No', 'No', 'No'
        ]
        colon2 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Plasma', '1500', '0.3', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        colon3 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Urine', '150', '5', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        liver1 = [
            'Liver', '111', f'<a id="{liver}" linktype="page">DCP/Liver Ref set Rapid set</a>', '50', '50', '100', '⁠',
            'Serum', '1,329', '0.01–0.5', 'Yes', 'No', 'No', 'No', 'No', 'Yes'
        ]
        liver2 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Plasma', '731', '0.2–0.5', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        dcp_liver1 = [
            'Liver', '111', 'DCP/Liver Ref set Validation set', '427', '432', '871', '⁠', 'Serum', '10,815',
            '0.01–1.0', 'Yes', 'No', 'No', 'No', 'No', 'No'
        ]
        dcp_liver2 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Plasma', '5,090', '0.2–0.5', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        a_lung1 = [
            'Lung', '115', f'<a id="{lung}" linktype="page">Lung Ref Set A Phase 2 Validation (retrospective)</a>',
            '268', '309', '577', '⁠', 'Serum', '3,695', '0.025–0.5', 'Yes', 'No', 'No', 'No', 'No', 'No'
        ]
        a_lung2 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Plasma', '5,267', '0.15–0.3', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        b_lung = [
            'Lung', '115', f'<a id="{lung}" linktype="page">Lung Ref Set B (retrospective)</a>', '86', '147', '233', '⁠',
            'Plasma', '3,846', '0.025–0.375', 'Yes', 'No', 'No', 'No', 'No', 'No'
        ]
        c_lung1 = [
            'Lung', '115', f'<a id="{lung}" linktype="page">Lung Ref Set C (prospective)</a>', '159', '195', '354', '⁠',
            'Serum', '6,430', '0.015–0.2', 'Yes', 'No', 'No', 'No', 'No', 'No'
        ]
        c_lung2 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Plasma', '6,787', '0.01–0.175', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        pancreas1 = [
            'Pancreas', '185', f'<a id="{pancreas}" linktype="page">Pancreatic cancer</a>', '100', '155', '255', '⁠',
            'Serum', '4,847', '0.1–0.8', 'Yes', 'No', 'No', 'Yes', 'No', 'No'
        ]
        pancreas2 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Plasma', '3,006', '0.2–0.8', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        prostate1 = [
            'Prostate', '274', f'<a id="{prostate}" linktype="page">Prostate cancer (from PCA3)</a>',
            '341', '559', '900', '⁠', 'Serum', '16,778', '0.075–0.5', 'Yes', 'No', 'No', 'No', 'No', 'Yes'
        ]
        prostate2 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Buffy coat', '864', '0.05–0.5', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        prostate3 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Whole urine', '771', '1.2–5.0', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        prostate4 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'EDTA plasma', '13,137', '0.1', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        prostate5 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Sediment/RNALater', '738', '0.035–1.5', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        prostate6 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Sediment/PBS', '486', '0.01–0.4', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        prostate7 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Supernatant', '1,493', '2.5–50', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        prostate8 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'PAXGene', '1,716', '"tubes"', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        panc2_1 = [
            'Pancreas', '342', f'<a id="{pancreas}" linktype="page">Panc Cyst</a>',
            '48', '270', '318', '⁠', 'Serum', '16,958', '0.1–0.3', 'Yes', 'No', 'No', 'No', 'No', 'Yes'
        ]
        panc2_2 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'EDTA plasma', '8,605', '0.1–0.3', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        panc2_3 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'EUS cystic fluid', '5,538', '0.05–0.1', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        panc2_4 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Surgical cystic fluid', '4,599', '0.1–0.6', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']

        blank = ['⁠' for i in range(16)]
        rows = [
            {'values': bbd},
            {'values': blank},
            {'values': breast1},
            {'values': breast2},
            {'values': blank},
            {'values': ovarian},
            {'values': blank},
            {'values': colon1},
            {'values': colon2},
            {'values': colon3},
            {'values': blank},
            {'values': liver1},
            {'values': liver2},
            {'values': blank},
            {'values': dcp_liver1},
            {'values': dcp_liver2},
            {'values': blank},
            {'values': a_lung1},
            {'values': a_lung2},
            {'values': b_lung},
            {'values': c_lung1},
            {'values': c_lung2},
            {'values': blank},
            {'values': pancreas1},
            {'values': pancreas2},
            {'values': blank},
            {'values': prostate1},
            {'values': prostate2},
            {'values': prostate3},
            {'values': prostate4},
            {'values': prostate5},
            {'values': prostate6},
            {'values': prostate7},
            {'values': prostate8},
            {'values': blank},
            {'values': panc2_1},
            {'values': panc2_2},
            {'values': panc2_3},
            {'values': panc2_4},
        ]
        table_block = TYPED_TABLE_BLOCK.to_python({'columns': columns, 'rows': rows})
        ref_sets.body.append(('typed_table', table_block))

    def handle(self, *args, **options):
        self.stdout.write('Rewriting the Specimen Reference Sets')

        old = getattr(settings, 'WAGTAILREDIRECTS_AUTO_CREATE', True)
        try:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = False
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = False

            site, home_page = set_site()
            ref_sets = home_page.get_descendants().filter(title='Specimen Reference Sets').first().specific
            assert ref_sets is not None

            self._clean_slate(ref_sets)

            brscw = self._create_ovarian_breast_page(ref_sets)
            breast = self._create_breast_page(ref_sets)
            bbd = self._create_bbd_page(ref_sets)
            lung = self._create_lung_page(ref_sets)
            colon = self._create_colon_page(ref_sets)
            prostate = self._create_prostate_page(ref_sets)
            liver = self._create_liver_page(ref_sets)
            pancreas = self._create_pancreas_page(ref_sets)

            self._add_table(ref_sets, brscw, breast, bbd, lung, colon, prostate, liver, pancreas)
            self._add_general_documents(ref_sets)

            ref_sets.save()
            for cache in caches:
                caches[cache].clear()
        finally:
            settings.WAGTAILREDIRECTS_AUTO_CREATE = old
            settings.WAGTAILSEARCH_BACKENDS['default']['AUTO_UPDATE'] = True
