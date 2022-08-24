# encoding: utf-8

'''🧫 EDRN Knowledge Environment Biomarkers: utilities.'''


from .constants import BMDB_URI_PREFIX


def qualify_biomarker_predicate(partial: str) -> str:
    '''Yield a fully-qualified predicate URI in the biomarker database namespace for the given
    ``partial`` predicate.
    '''
    return BMDB_URI_PREFIX + partial
