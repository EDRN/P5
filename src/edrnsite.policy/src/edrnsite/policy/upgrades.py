# -*- coding: utf-8 -*-

from . import PACKAGE_NAME
import logging

PROFILE = 'profile-' + PACKAGE_NAME + ':default'


def reloadViewlets(setupTool, logger=None):
    if logger is None:
        logger = logging.getLogger(PACKAGE_NAME)
    setupTool.runImportStepFromProfile(PROFILE, 'viewlets')


# Boilerplate from paster template; leaving for posterity:
# from plone.app.upgrade.utils import loadMigrationProfile
# def reload_gs_profile(context):
#    loadMigrationProfile(context, 'profile-edrnsite.policy:default',)
