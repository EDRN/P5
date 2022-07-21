#!/usr/bin/env python
# encoding: utf-8
# Copyright 2022 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from collective.exportimport.export_content import ExportContent
from collective.exportimport.export_other import ExportDefaultPages
import sys, logging


logging.basicConfig(level=logging.INFO, format='%(levelname)-8s %(message)s')
app = globals().get('app', None)  # ``app`` comes from ``instance run`` magic.

_types = [
    'Plone Site', 'eke.knowledge.collaborationsfolder', 'eke.knowledge.collaborativegroupfolder',
    'eke.knowledge.collaborativegroupindex', 'Event', 'File', 'Folder', 'eke.knowledge.groupspacefolder',
    'eke.knowledge.groupspaceindex', 'Image', 'Link', 'News Item', 'Document'
]


def _export(portal):
    portal.REQUEST.form.setdefault('form.submitted', True)
    ExportContent(portal, portal.REQUEST)(_types, '/edrn', -1, 2, 1, True, False)
    ExportDefaultPages(portal, portal.REQUEST)(True)


def _main(app):
    portal = app['edrn']
    _export(portal)
    return True


def main(argv):
    try:
        global app
        _main(app)
    except Exception as ex:
        logging.exception(u'This is most unfortunate: %s', unicode(ex))
        return False
    return True


if __name__ == '__main__':
    # The [2:] works around plone.recipe.zope2instance-4.2.6's lame bin/interpreter script issue
    sys.exit(0 if main(sys.argv[2:]) is True else -1)
