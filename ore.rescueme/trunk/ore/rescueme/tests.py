"""
$Id: $
"""

import unittest
import re

from zope.testing import doctest, renormalizing
#from zope.app.testing import placelesssetup

def test_suite():
    import testing
    return unittest.TestSuite((
        doctest.DocFileSuite(
            'readme.txt',
            setUp=testing.setUp, tearDown=testing.tearDown,
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
            globs=testing.doctest_ns
            )))
