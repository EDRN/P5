# -*- coding: utf-8 -*-

from . import PACKAGE_NAME
import logging

PROFILE = 'profile-' + PACKAGE_NAME + ':default'


def reloadViewlets(setupTool, logger=None):
    setupTool.runImportStepFromProfile(PROFILE, 'viewlets')


def reloadRegistry(setupTool, logger=None):
    setupTool.runImportStepFromProfile(PROFILE, 'plone.app.registry')


# Boilerplate from paster template; leaving for posterity:
# from plone.app.upgrade.utils import loadMigrationProfile
# def reload_gs_profile(context):
#    loadMigrationProfile(context, 'profile-edrnsite.policy:default',)
