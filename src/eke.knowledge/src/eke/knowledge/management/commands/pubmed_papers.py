# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: PubMed paper retreival.'''

from Bio import Entrez
from botocore import UNSIGNED
from botocore.config import Config
from contextlib import closing
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from edrnsite.controls.models import Informatics
from eke.knowledge.models import Publication, PMCID
from urllib.error import HTTPError
from wagtail.models import Site
import os, os.path, time, logging, boto3, botocore.exceptions


class Command(BaseCommand):
    help = 'Downloads all PubMed papers in the portal'

    def add_arguments(self, parser):
        parser.add_argument('--dir', default='papers', help='Where to save the papers')
        parser.add_argument('--batch-size', default=97, type=int, help='How many papers to get at a time [%(default)d]')
        parser.add_argument('--delay', default=3.0, type=float, help="Seconds to wait 'txit retreivals [%(default)f]")

    def configure_entrez(self):
        informatics = Informatics.for_site(Site.objects.filter(is_default_site=True).first())
        Entrez.tool = informatics.entrez_id
        Entrez.email = informatics.entrez_email

    def divide(self, sequence: list, batch_size: int) -> list:
        while len(sequence) > 0:
            group, sequence = sequence[:batch_size], sequence[batch_size:]
            yield group

    def get_fn(self, output_dir: str, pmid: str) -> str:
        return os.path.join(output_dir, pmid) + '.txt'

    def filter_existing(self, output_dir: str, pmids: set) -> set:
        needed = set()
        while len(pmids) > 0:
            pmid = pmids.pop()
            if not os.path.isfile(self.get_fn(output_dir, pmid)):
                needed.add(pmid)
        return needed

    def find_pmcids(self, output_dir: str, bs: int, delay: float) -> set:
        pmcids = set()

        pmids = set(Publication.objects.values_list('pubMedID', flat=True).distinct())
        self.stdout.write(f'We currently have {len(pmids)} PMIDs in the portal')
        pmids = self.filter_existing(output_dir, pmids)
        self.stdout.write(f'Filtering those already in {output_dir} leaves {len(pmids)} to find matching PMC IDs')
        for item in PMCID.objects.filter(pmid__in=pmids):
            pmcids.add((item.pmid, item.pmcid))
            pmids.remove(item.pmid)

        self.stdout.write(f'Filtering the cached PMC IDs that leaves {len(pmids)} to look up')
        pmids = list(pmids)
        for group in self.divide(pmids, bs):
            try:
                with closing(Entrez.elink(dbfrom='pubmed', db='pmc', id=group)) as ef:
                    records = Entrez.read(ef)
                    for record in records:
                        pmid = record['IdList'][0]
                        try:
                            pmcid = record['LinkSetDb'][0]['Link'][0]['Id']
                            try:
                                PMCID.objects.get_or_create(pmid=pmid, pmcid=pmcid)
                            except IntegrityError:
                                pass
                        except IndexError:
                            pmcid = None
                        pmcids.add((pmid, pmcid))
                    self.stdout.write(f'Processed {len(pmcids)}…')
            except HTTPError as ex:
                self.stderr.write(f'HTTPError {ex.getcode()} with batch {repr(group)}; pressing on!')
            finally:
                time.sleep(delay)
        self.stdout.write(f'Completed matching up {len(pmcids)}')
        return pmcids

    def get_oa_obj_name(self, pmcid: str) -> str:
        return f'oa_noncomm/txt/all/PMC{pmcid}.txt'

    def download_files(self, output_dir: str, pmcids: set, bs: int, delay: float):
        s3 = boto3.client('s3', config=Config(region_name='us-east-1', signature_version=UNSIGNED))
        for pmid, pmcid in pmcids:
            src = self.get_oa_obj_name(pmcid) if pmcid else None
            dest = self.get_fn(output_dir, pmid)
            with open(dest, 'wb') as f:
                if src is None:
                    self.stdout.write(f'{pmid} has no matching PMC ID')
                    response = f'PMID = {pmid}\nPMCID = «no-match»\n'.encode('utf-8')
                    f.write(response)
                else:
                    try:
                        s3.download_fileobj('pmc-oa-opendata', src, f)
                        self.stdout.write(f'Successfully retrieved {pmid}')
                    except botocore.exceptions.ClientError:
                        response = f'PMID = {pmid}\nPMCID = {pmcid}\n«not available»\n'.encode('utf-8')
                        f.write(response)
                        self.stdout.write(f'{pmid} is not available')
                    except Exception as ex:
                        os.unlink(dest)
                        self.stderr.write(f'Error {repr(ex)} on {pmid}; you can retry')

    def handle(self, *args, **options):
        verbosity = int(options['verbosity'])
        root_logger = logging.getLogger('')
        if verbosity >= 3:
            root_logger.setLevel(logging.DEBUG)

        output_dir = os.path.abspath(options['dir'])
        os.makedirs(output_dir, exist_ok=True)
        bs, delay = options['batch_size'], options['delay']
        if bs <= 0: raise ValueError('Batch size must be positive')
        if delay <= 0: raise ValueError('Delay must be positive')

        self.stdout.write(f'Starting paper download to {output_dir}')
        self.configure_entrez()
        pmcids = self.find_pmcids(output_dir, bs, delay)
        self.download_files(output_dir, pmcids, bs, delay)
