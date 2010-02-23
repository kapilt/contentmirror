
import unittest
from zope import component, interface
from zope.testing import doctest

from ore.contentmirror.testing import setUp as _setUp
from ore.contentmirror.testing import tearDown, doctest_ns, MockField

from mirror.pfg import transform, interfaces

class TALESString(MockField):
    interface.implements(interfaces.ITALESStringField)

def setUp(test):
    _setUp(test)
    component.provideAdapter(transform.TALESStringTransform)

def test_suite():
    ns = dict(doctest_ns)
    ns['TALESString'] = TALESString

    return unittest.TestSuite(
        doctest.DocFileSuite(
        'readme.txt',
        setUp=setUp, tearDown=tearDown,
        optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
        globs=ns
        ),)
