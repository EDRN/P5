# encoding: utf-8

'''🧬 EDRN Site Policy: RDF utilities for policy-level management commands.'''

from eke.knowledge.models import RDFSource
import importlib.resources


_testPkg       = 'eke.knowledge'
_cdeOrgans     = 'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/body-systems/@@rdf'
_testOrgans    = f'file:{importlib.resources.resource_filename(_testPkg, "data/body-systems.rdf")}'
_cdeDiseases   = 'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/diseases/@@rdf'
_testDiseases  = f'file:{importlib.resources.resource_filename(_testPkg, "data/diseases.rdf")}'
_bmdbResources = 'https://bmdb.jpl.nasa.gov/rdf/resources?all=yeah'
_testResources = f'file:{importlib.resources.resource_filename(_testPkg, "data/misc-resources.rdf")}'
_cdePubs       = 'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/publications/@@rdf'
_bmdbPubs      = 'https://bmdb.jpl.nasa.gov/rdf/publications?all=yeah'
_testPubs      = f'file:{importlib.resources.resource_filename(_testPkg, "data/pubs.rdf")}'
_sites         = 'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/sites/@@rdf'
_testSites     = f'file:{importlib.resources.resource_filename(_testPkg, "data/sites.rdf")}'
_people        = 'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/registered-person/@@rdf'
_testPeople    = f'file:{importlib.resources.resource_filename(_testPkg, "data/people.rdf")}'
_protocols     = 'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/protocols/@@rdf'
_testProtos    = f'file:{importlib.resources.resource_filename(_testPkg, "data/protocols.rdf")}'
_data          = 'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/labcas/@@rdf'
_testData      = f'file:{importlib.resources.resource_filename(_testPkg, "data/labcas.rdf")}'

_bio       = 'https://bmdb.jpl.nasa.gov/rdf/biomarkers'
_bioOrgans = 'https://bmdb.jpl.nasa.gov/rdf/biomarker-organs'
_bioMuta   = 'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/fixed-biomuta/@@rdf'
_testBio   = f'file:{importlib.resources.resource_filename("eke.biomarkers", "data/biomarkers.rdf")}'
_testBO    = f'file:{importlib.resources.resource_filename("eke.biomarkers", "data/bio-org.rdf")}'
_testBM    = f'file:{importlib.resources.resource_filename("eke.biomarkers", "data/muta.rdf")}'


# Sources of RDF Data
# -------------------
# 
# This dictionary is a mapping from kind of data (str) to a mapping of whether we're in full
# (True) or "lite" (False) mode, to a sequence of RDF sources for that mode and kind.

RDF_SOURCES = {
    'publications': {
        True: [
            RDFSource(name='Cancer Data Expo', url=_cdePubs, active=True),
            RDFSource(name='Focus BMDB', url=_bmdbPubs, active=True),
            RDFSource(name='Test Pubs', url=_testPubs, active=False),
        ],
        False: [
            RDFSource(name='Cancer Data Expo', url=_cdePubs, active=False),
            RDFSource(name='Focus BMDB', url=_bmdbPubs, active=False),
            RDFSource(name='Test Pubs', url=_testPubs, active=True),
        ]
    },
    'body-systems': {
        True: [
            RDFSource(name='Cancer Data Expo', url=_cdeOrgans, active=True),
            RDFSource(name='Test Organs', url=_testOrgans, active=False),
        ],
        False: [
            RDFSource(name='Cancer Data Expo', url=_cdeOrgans, active=False),
            RDFSource(name='Test Organs', url=_testOrgans, active=True),
        ]
    },
    'diseases': {
        True: [
            RDFSource(name='Cancer Data Expo', url=_cdeDiseases, active=True),
            RDFSource(name='Test Diseases', url=_testDiseases, active=False)
        ],
        False: [
            RDFSource(name='Cancer Data Expo', url=_cdeDiseases, active=False),
            RDFSource(name='Test Diseases', url=_testDiseases, active=True)
        ]
    },
    'resources': {
        True: [
            RDFSource(name='Focus BMDB', url=_bmdbResources, active=True),
            RDFSource(name='Test Resources', url=_testResources, active=False),
        ],
        False: [
            RDFSource(name='Focus BMDB', url=_bmdbResources, active=False),
            RDFSource(name='Test Resources', url=_testResources, active=True),
        ]
    },
    'sites': {
        True: [
            RDFSource(name='Cancer Data Expo Sites', url=_sites, active=True),
            RDFSource(name='Cancer Data Expo People', url=_people, active=True),
            RDFSource(name='Test Sites', url=_testSites, active=False),
            RDFSource(name='Test People', url=_testPeople, active=False),
        ],
        False: [
            RDFSource(name='Cancer Data Expo Sites', url=_sites, active=False),
            RDFSource(name='Cancer Data Expo People', url=_people, active=False),
            RDFSource(name='Test Sites', url=_testSites, active=True),
            RDFSource(name='Test People', url=_testPeople, active=True),
        ],
    },
    'protocols': {
        True: [
            RDFSource(name='Cancer Data Expo', url=_protocols, active=True),
            RDFSource(name='Test Protocols', url=_testProtos, active=False),
        ],
        False: [
            RDFSource(name='Cancer Data Expo', url=_protocols, active=False),
            RDFSource(name='Test Protocols', url=_testProtos, active=True),
        ]
    },
    'data': {
        True: [
            RDFSource(name='Cancer Data Expo', url=_data, active=True),
            RDFSource(name='Test Protocols', url=_testData, active=False),
        ],
        False: [
            RDFSource(name='Cancer Data Expo', url=_data, active=False),
            RDFSource(name='Test Protocols', url=_testData, active=True),
        ]
    },
    'biomarkers': {
        True: [
            RDFSource(name='Focus BMDB Biomarkers', url=_bio, active=True),
            RDFSource(name='Focus BMDB Biomarker-Organs', url=_bioOrgans, active=True),
            RDFSource(name='Cancer Data Expo Mutations', url=_bioMuta, active=True),
            RDFSource(name='Test Biomarkers', url=_testBio, active=False),
            RDFSource(name='Test Biomarker-Organs', url=_testBO, active=False),
            RDFSource(name='Test Mutations', url=_testBM, active=False),
        ],
        False: [
            RDFSource(name='Focus BMDB Biomarkers', url=_bio, active=False,),
            RDFSource(name='Focus BMDB Biomarker-Organs', url=_bioOrgans, active=False,),
            RDFSource(name='Cancer Data Expo Mutations', url=_bioMuta, active=False,),
            RDFSource(name='Test Biomarkers', url=_testBio, active=True),
            RDFSource(name='Test Biomarker-Organs', url=_testBO, active=True),
            RDFSource(name='Test Mutations', url=_testBM, active=True),
        ]
    }
}
