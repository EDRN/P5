# encoding: utf-8

'''😌 EDRN Site Content: rewrite refence sets page.'''

from django.conf import settings
from django.core.cache import caches
from django.core.management.base import BaseCommand
from edrnsite.content.models import FlexPage
from edrnsite.policy.management.commands.utils import set_site
from edrnsite.streams.blocks import TYPED_TABLE_BLOCK
from eke.knowledge.models import Protocol
from wagtail.documents.models import Document
from wagtail.models import Page
from wagtail.rich_text import RichText


class Command(BaseCommand):
    help = 'Rewrite the Specimens Reference Sets pages'

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
            {'type': 'rich_text', 'heading': 'Protocol ID'},
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
        bbd_protocol = Protocol.objects.filter(slug='331-benign-breast-disease-team-project').first()
        assert bbd_protocol is not None
        bbd = [
            'Breast', f'<a id="{bbd_protocol.pk}" linktype="page">331</a>',
            f'<a id="{bbd}" linktype="page">Benign Breast Disease</a>',
            '30', '62', '92', 'BBD that progressed to cancer BBD controls', 'Tissue slides',
            '9,256', '"each"', 'No, at Kansas', 'N/A', '⁠', '✓', '⁠', '✓'
        ]
        breast_protocol = Protocol.objects.filter(slug='121-standard-specimen-reference-set-breast-cancer-and-imaging').first()
        assert breast_protocol is not None
        breast1 = [
            'Breast', f'<a id="{breast_protocol.pk}" linktype="page">121</a>',
            f'<a id="{breast}" linktype="page">Breast</a>',
            '262', '570', '832', 'Pre-diagnosis specimens, DCIS cases, Invasive cancer cases, LCIS cases, Benign→later cancer cases, Normal→later cancer cases, Benign Disease Atypia controls, Benign Disease non-Atypia controls, Normal controls',
            'Serum', '16,444', '0.01–0.8', '✓', '⁠', '⁠', '✓', '⁠', '✓'
        ]
        breast2 = [
            '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Plasma', '16,169', '0.01–0.9', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠'
        ]
        women_protocol = Protocol.objects.filter(slug='118-biomarker-reference-sets-for-cancers-in-women').first()
        assert women_protocol is not None
        ovarian = [
            'Ovarian & Breast', f'<a id="{women_protocol.pk}" linktype="page">118</a>',
            f'<a id="{brscw}" linktype="page">Cancers in women-BRSCW</a>',
            '441', '95', '536', 'Cases (pooled), controls (pooled)', 'Serum', '105 sets', '0.3',
            '✓', '⁠', '⁠', '⁠', '⁠', '⁠'
        ]
        colon_protocol = Protocol.objects.filter(slug='251-standard-specimen-reference-set-colon').first()
        assert colon_protocol is not None
        colon1 = [
            'Colon', f'<a id="{colon_protocol.pk}" linktype="page">251</a>',
            f'<a id="{colon}" linktype="page">Colon cancer</a>', '50', '100', '150', '⁠', 'Serum',
            '2,100', '0.3', '✓', '⁠', '⁠', '⁠', '⁠', '⁠'
        ]
        colon2 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Plasma', '1500', '0.3', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        colon3 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Urine', '150', '5', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        liver_protocol = Protocol.objects.filter(slug='111-validation-of-serum-markers-for-the-early-detection-of-hepatocellular-carcinoma').first()
        assert liver_protocol is not None
        liver1 = [
            'Liver', f'<a id="{liver_protocol.pk}" linktype="page">111</a>',
            f'<a id="{liver}" linktype="page">DCP/Liver Ref set Rapid set</a>', '50', '50', '100', '⁠',
            'Serum', '1,329', '0.01–0.5', '✓', '⁠', '⁠', '⁠', '⁠', '✓'
        ]
        liver2 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Plasma', '731', '0.2–0.5', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        dcp_liver1 = [
            'Liver', f'<a id="{liver_protocol.pk}" linktype="page">111</a>',
            'DCP/Liver Ref set Validation set', '427', '432', '871', '⁠', 'Serum', '10,815',
            '0.01–1.0', '✓', '⁠', '⁠', '⁠', '⁠', '⁠'
        ]
        dcp_liver2 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Plasma', '5,090', '0.2–0.5', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        lung_protocol = Protocol.objects.filter(slug='115-standard-specimen-reference-set-lung').first()
        a_lung1 = [
            'Lung', f'<a id="{lung_protocol.pk}" linktype="page">115</a>',
            f'<a id="{lung}" linktype="page">Lung Ref Set A Phase 2 Validation (retrospective)</a>',
            '268', '309', '577', '⁠', 'Serum', '3,695', '0.025–0.5', '✓', '⁠', '⁠', '⁠', '⁠', '⁠'
        ]
        a_lung2 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Plasma', '5,267', '0.15–0.3', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        b_lung = [
            'Lung', f'<a id="{lung_protocol.pk}" linktype="page">115</a>',
            f'<a id="{lung}" linktype="page">Lung Ref Set B (retrospective)</a>', '86', '147', '233', '⁠',
            'Plasma', '3,846', '0.025–0.375', '✓', '⁠', '⁠', '⁠', '⁠', '⁠'
        ]
        c_lung1 = [
            'Lung', f'<a id="{lung_protocol.pk}" linktype="page">115</a>',
            f'<a id="{lung}" linktype="page">Lung Ref Set C (prospective)</a>', '159', '195', '354', '⁠',
            'Serum', '6,430', '0.015–0.2', '✓', '⁠', '⁠', '⁠', '⁠', '⁠'
        ]
        c_lung2 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Plasma', '6,787', '0.01–0.175', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        pancreas_protocol = Protocol.objects.filter(slug='185-standard-specimen-reference-set-pancreatic').first()
        assert pancreas_protocol is not None
        pancreas1 = [
            'Pancreas', f'<a id="{pancreas_protocol.pk}" linktype="page">185</a>',
            f'<a id="{pancreas}" linktype="page">Pancreatic cancer</a>', '100', '155', '255', '⁠',
            'Serum', '4,847', '0.1–0.8', '✓', '⁠', '⁠', '✓', '⁠', '⁠'
        ]
        pancreas2 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Plasma', '3,006', '0.2–0.8', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        pca_protocol = Protocol.objects.filter(slug='274-pca3-validation-study-and-urinary-reference-set').first()
        assert pca_protocol is not None
        prostate1 = [
            'Prostate', f'<a id="{pca_protocol.pk}" linktype="page">274</a>',
            f'<a id="{prostate}" linktype="page">Prostate cancer (from PCA3)</a>',
            '341', '559', '900', '⁠', 'Serum', '16,778', '0.075–0.5', '✓', '⁠', '⁠', '⁠', '⁠', '✓'
        ]
        prostate2 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Buffy coat', '864', '0.05–0.5', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        prostate3 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Whole urine', '771', '1.2–5.0', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        prostate4 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'EDTA plasma', '13,137', '0.1', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        prostate5 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Sediment/RNALater', '738', '0.035–1.5', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        prostate6 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Sediment/PBS', '486', '0.01–0.4', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        prostate7 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'Supernatant', '1,493', '2.5–50', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        prostate8 = ['⁠', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠', 'PAXGene', '1,716', '"tubes"', '⁠', '⁠', '⁠', '⁠', '⁠', '⁠']
        pancreas_protocol = Protocol.objects.filter(slug='342-pancreatic-cystic-fluid-reference-set').first()
        assert pancreas_protocol is not None
        panc2_1 = [
            'Pancreas', f'<a id="{pancreas_protocol.pk}" linktype="page">342</a>',
            f'<a id="{pancreas}" linktype="page">Panc Cyst</a>',
            '48', '270', '318', '⁠', 'Serum', '16,958', '0.1–0.3', '✓', '⁠', '⁠', '⁠', '⁠', '✓'
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
