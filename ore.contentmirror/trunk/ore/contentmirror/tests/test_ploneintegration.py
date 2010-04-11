import unittest
import os


def test_suite():
    suite = unittest.TestSuite()
    if os.environ.get("NO_PLONE"):
        return suite
    try:
        from ore.contentmirror.ptests import test_copymove
        from ore.contentmirror.ptests import test_position
        from ore.contentmirror.ptests import test_content
    except ImportError, e:
        print "Plone Tests Disabled", e
        return suite

    suite.addTest(test_copymove.test_suite())
    suite.addTest(test_position.test_suite())
    suite.addTest(test_content.test_suite())
    return suite
