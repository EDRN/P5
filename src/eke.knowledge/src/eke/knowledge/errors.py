# encoding: utf-8

u'''Exceptions and errors.'''


class IngestError(Exception):
    u'''Abstract exception for RDF ingest.'''
    def __init__(self, message):
        super(IngestError, self).__init__(message)


class RDFTypeMismatchError(IngestError):
    u'''Error when RDF predicates doesn't match expected type.'''
    def __init__(self, expected, butGot):
        u'''Indicate an error with the ``expected`` type URI against the type URI ``butGot``.'''
        super(RDFTypeMismatchError, self).__init__(u'Expected type URI {} but got type {}'.format(expected, butGot))


class TitlePredicateMissingError(IngestError):
    u'''Error when required Dublin Core "title" predicate is missing. Everything needs a title.'''
    def __init__(self):
        super(TitlePredicateMissingError, self).__init__(u'Dublin Core "title" term missing; is required')


class IngestDisabled(IngestError):
    u'''An "exception" (not really) saying ingest is turned off'''
    def __init__(self, obj):
        super(IngestDisabled, self).__init__(u'Ingest disabled on {}'.format(u'/'.join(obj.getPhysicalPath())))
