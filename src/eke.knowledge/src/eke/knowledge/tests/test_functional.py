# encoding: utf-8

u'''Functional tests'''

from eke.knowledge import PACKAGE_NAME
from eke.knowledge.testing import EKE_KNOWLEDGE_FUNCTIONAL_TESTING as layer
from plone.testing import layered
import doctest, unittest

_optionFlags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE | doctest.REPORT_ONLY_FIRST_FAILURE)


def test_suite():
    return unittest.TestSuite([
        layered(doctest.DocFileSuite('README.rst', package=PACKAGE_NAME, optionflags=_optionFlags), layer),
    ])


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
