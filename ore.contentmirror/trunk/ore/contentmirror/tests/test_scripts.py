import new
import sys
import unittest
from zope import interface

from ore.contentmirror import schema
from base import IntegrationTest, SampleContent, CustomContent


class MockApp(object):

    results = []

    class Portal(object):

        class portal_catalog(object):

            @staticmethod
            def unrestrictedSearchResults(**kw):
                return map(MockApp.Brain, MockApp.results)

    class acl_users(object):

        @classmethod
        def getUserById(cls, id):
            return None

    class Brain(object):

        def __init__(self, ob):
            self.ob = ob

        def getObject(self):
            return self.ob

    @classmethod
    def unrestrictedTraverse(cls, path):
        return cls.Portal


class BulkScriptTest(IntegrationTest):

    module_key = "AccessControl.SecurityManagement"
    cleanup_modules = False

    def setUp(self):
        access_control = new.module("AccessControl")
        security_manager = new.module(self.module_key)
        security_manager.newSecurityManager = lambda x, y: None
        if not self.module_key in sys.modules:
            sys.modules["AccessControl"] = access_control
            sys.modules[self.module_key] = security_manager
            self.cleanup_modules = True
        super(BulkScriptTest, self).setUp()
        snippet = """
        <ore:mirror content='%s'/>
        """ % (self.sample_content)
        self._load(snippet)
        schema.metadata.create_all()
        interface.classImplementsOnly(CustomContent, ())

    def tearDown(self):
        schema.metadata.drop_all(checkfirst=True)
        if self.cleanup_modules:
            del sys.modules[self.module_key]
            del sys.modules["AccessControl"]
        super(BulkScriptTest, self).tearDown()

    def testBulk(self):
        c1 = SampleContent("a")
        c2 = SampleContent("b")
        c2.uid = ""
        c3 = CustomContent("c")
        MockApp.results = [c1, c2, c3]
        from ore.contentmirror.bulk import main
        main(MockApp, "portal", 1)


class DDLScriptTest(IntegrationTest):
    pass


class JsonSchemaScriptTest(IntegrationTest):
    pass


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
