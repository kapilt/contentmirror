import unittest


def test_suite():
    try:
        from ore.contentmirror.ptests import test_copymove
        from ore.contentmirror.ptests import test_position
    except ImportError, e:
        print "Plone Tests Disabled", e
        return unittest.TestSuite()

    suite = unittest.TestSuite()
    suite.addTest(test_copymove.test_suite())
    suite.addTest(test_position.test_suite())
    return suite
