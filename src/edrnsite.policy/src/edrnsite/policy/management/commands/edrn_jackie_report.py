# encoding: utf-8

'''🧬 EDRN Site: Jackie's report.'''

from django.core.management.base import BaseCommand
from eke.knowledge.models import Protocol
from eke.biomarkers.biomarker import Biomarker, BiomarkerBodySystem
from django.db.models.functions import Lower
import argparse, sys, csv


class Command(BaseCommand):
    '''The EDRN Jackie's report command.'''

    help = "Produce a spreadsheet like Jackie's report"

    protocols = [
        24,
        52,
        57,
        76,
        79,
        82,
        83,
        108,
        109,
        110,
        111,
        114,
        115,
        118,
        119,
        120,
        121,
        122,
        126,
        129,
        136,
        137,
        138,
        185,
        192,
        193,
        195,
        196,
        239,
        244,
        251,
        274,
        281,
        282,
        312,
        316,
        320,
        322,
        327,
        330,
        331,
        333,
        342,
        347,
        348,
        351,
        353,
        354,
        381,
        382,
        421,
        423,
        427,
        428,
        430,
        434,
        446,
        450,
        452,
        454,
        456,
        461,
        462,
        464,
        467,
        494,
        497,
        498,
        502,
        506,
        507,
        510,
        513,
        519
    ]

    phases = {
        1: 'Phase 1: Preclinical Exploratory',
        2: 'Phase 2: Clinical Assay and Validation',
        3: 'Phase 3: Retrospective Longitudinal',
        4: 'Phase 4: Prospective Screening'
    }

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            '--protocols',
            help=f"Comma-seprated protocol IDs to report on (defaults to Jackie's set of {len(self.protocols)})"
        )
        parser.add_argument(
            'outfile', help='Output CSV file, defaults to stdout', default=sys.stdout, nargs='?',
            type=argparse.FileType(mode='w', encoding='UTF-8')
        )

    def make_report(self, outfile, protocolIDs: list[int]):
        with outfile:
            writer = csv.writer(outfile)
            writer.writerow([
                'ProtocolID', 'protocolName', 'ProtocolNameShort', 'StudyType', 'LeadingSiteID', 'LeadingSiteName',
                'firstname', 'lastname', 'BiomarkerPhaseDescription', 'BiomarkersEvaluated', 'CALocations',
                'CALocationsName', 'CALocationsOtherSpecify', 'GroupName'
            ])
            for protocolID in protocolIDs:
                protocol = Protocol.objects.filter(protocolID=protocolID).first()
                if not protocol:
                    self.stderr.write(f'Protocol {protocolID} not found; skipping')
                lead_site = protocol.leadInvestigatorSite
                fn, ln = protocol.piName.split(',')[1].strip(), protocol.piName.split(',')[0].strip()
                phase = self.phases.get(protocol.phasedStatus, 'NULL')
                bms = Biomarker.objects.filter(protocols=protocol).live().order_by(Lower('title'))
                organs = set()
                for bm in bms:
                    organs.update([
                        i.strip() for i in BiomarkerBodySystem.objects.filter(biomarker=bm).values_list('title', flat=True)
                    ])
                organs = list(organs)
                organs.sort()
                writer.writerow([
                    protocolID, protocol.title, protocol.abbreviation, protocol.kind,
                    lead_site.dmccSiteID, lead_site.title, fn, ln,
                    phase,
                    ', '.join([bm.title.strip() for bm in bms]), '?', ', '.join(organs), '?',
                    protocol.collaborativeGroup
                ])

    def handle(self, *args, **options):
        '''Handle the EDRN `edrn_jackie_report` command.'''
        if not options['protocols']:
            protocols = self.protocols
        else:
            protocols = [int(i.strip()) for i in options['protocols'].split(',')]
        self.make_report(options['outfile'], protocols)
