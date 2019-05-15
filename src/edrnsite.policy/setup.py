# -*- coding: utf-8 -*-
"""Installer for the edrnsite.policy package."""

from setuptools import find_packages
from setuptools import setup


long_description = '\n\n'.join([
    open('README.rst').read(),
    open('CONTRIBUTORS.rst').read(),
    open('CHANGES.rst').read(),
])


setup(
    name='edrnsite.policy',
    version='5.0.0',
    description="EDRN site orchestration and policies",
    long_description=long_description,
    # Get more from https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 5.0",
        "Framework :: Plone :: 5.1",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: Apache Software License",
    ],
    keywords='Early Detection cancer Python Plone',
    author='Sean Kelly',
    author_email='kelly@seankelly.biz',
    url='https://pypi.python.org/pypi/edrnsite.policy',
    license='ALv2',
    packages=find_packages('src', exclude=['ez_setup']),
    namespace_packages=['edrnsite'],
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
        'setuptools',
        'collective.captchacontactinfo',
        'edrn.theme',
        'edrnsite.portlets',
        'eea.facetednavigation',
        'eke.knowledge',
        'pas.plugins.ldap',
        'plone.api>=1.8.4',
        'Products.CMFPlone',
        'Products.GenericSetup>=1.8.2',
        'z3c.jbot',
    ],
    extras_require={
        'test': [
            'plone.app.testing',
            # Plone KGS does not use this version, because it would break
            # Remove if your package shall be part of coredev.
            # plone_coredev tests as of 2016-04-01.
            'plone.testing>=5.0.0',
            'plone.app.contenttypes',
            'plone.app.robotframework[debug]',
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    [console_scripts]
    update_locale = edrnsite.policy.locales.update:update_locale
    """,
)
