# encoding: utf-8

'''🧫 EDRN Knowledge Environment Biomarkers: constants.'''

from enum import Enum, auto


BMDB_URI_PREFIX                  = 'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#'
HGNC_PREDICATE_URI               = BMDB_URI_PREFIX + 'HgncName'
PRIVATE_BIOMARKER_BOILERPLATE_ID = 'private-biomarker-admonition'


# This maps from an organ name used in the Focus Biomarker Database to a collaborative group name.
# It'd probably be better to model this (Django model) in the database so we can update these without
# changing software, but this mapping hasn't itself changed in over a dozen years.

ORGAN_GROUPS = {
    'Breast'               : 'Breast and Gynecologic Cancers Research Group',
    'Ovary'                : 'Breast and Gynecologic Cancers Research Group',
    'Colon'                : 'G.I. and Other Associated Cancers Research Group',
    'Esophagus'            : 'G.I. and Other Associated Cancers Research Group',
    'Liver'                : 'G.I. and Other Associated Cancers Research Group',
    'Pancreas'             : 'G.I. and Other Associated Cancers Research Group',
    'Lung'                 : 'Lung and Upper Aerodigestive Cancers Research Group',
    'Prostate'             : 'Prostate and Urologic Cancers Research Group',
    'Bladder'              : 'Prostate and Urologic Cancers Research Group',
    'Head & neck, NOS'     : 'Lung and Upper Aerodigestive Cancers Research Group',
    # Used only in testing :
    'Rectum'               : 'G.I. and Other Associated Cancers Research Group'
}


class DepictableSections(Enum):
    '''The different parts of a biomarker than can be depicted in a browser.'''

    BASICS       = auto()  # The basic attributes like name, description, aliases
    ORGANS       = auto()  # Organ-specific information, including organ-protocol links and organ-publication links
    STUDIES      = auto()  # Protocol-specific information at the biomarker-protocol level
    PUBLICATIONS = auto()  # Publication-specific inforation
    RESOURCES    = auto()  # Additiona resources like gene links, proteome databases, etc.
    SUPPLEMENTAL = auto()  # Supplemental organ-specific information, like specificity, positive-predictive value, …
    DATA_COL     = auto()  # Scientific data collections
