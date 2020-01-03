# -*- coding: utf-8 -*-

u'''EDRN Theme: the theme package for the Early Detection Research Network (EDRN).

This is a Plone theme (for Plone version 5) that provides the look-and-feel
off the National Cancer Institute for the Early Detection Research Network
websites—or at least *if they happen to run Plone 5*.

This can be installed onto any Plone 5 site by including its package in a Zope
instance's eggs (typically in the eggs list of the
`plone.recipe.zope2instance` in a Buildout) or by depending on this package in
*another* package that goes into the buildout.
'''

from zope.i18nmessageid import MessageFactory


_ = MessageFactory('edrn.theme')
