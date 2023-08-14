# encoding: utf-8

'''📐 EDRN Metrics: utilities.'''


from eke.biomarkers.biomarker import Biomarker, BiomarkerBodySystem, BodySystemStudy
from eke.knowledge.models import DataCollection, Publication
from django.db.models import Count


def find_pubs_without_pis():
    return set([i for i in Publication.objects.annotate(num_sites=Count('site_that_wrote_this')).filter(num_sites=0)])


def find_data_without_biomarkers():
    data = set(DataCollection.objects.values_list('pk', flat=True))
    data -= set(Biomarker.objects.values_list('science_data', flat=True))
    data -= set(BiomarkerBodySystem.objects.values_list('science_data', flat=True))
    data -= set(BodySystemStudy.objects.values_list('science_data', flat=True))
    return DataCollection.objects.filter(pk__in=data)


def find_data_collections_without_pis():
    return DataCollection.objects.filter(investigator_name='')


def find_biomarkers_without_publications():
    publess = []
    for biomarker in Biomarker.objects.all():
        if biomarker.publications.count() > 0: continue
        for bbs in biomarker.biomarker_body_systems.all():
            if bbs.publications.count() > 0: continue
            for bss in bbs.body_system_studies.all():
                if bss.publications.count() > 0: continue
        publess.append(biomarker)
    return publess


def find_biomarkers_without_data():
    dataless = []
    for biomarker in Biomarker.objects.all():
        if biomarker.science_data.count() > 0: continue
        for bbs in biomarker.biomarker_body_systems.all():
            if bbs.science_data.count() > 0: continue
            for bss in bbs.body_system_studies.all():
                if bss.science_data.count() > 0: continue
        dataless.append(biomarker)
    return dataless
