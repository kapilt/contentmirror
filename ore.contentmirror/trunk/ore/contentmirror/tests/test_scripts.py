import new
import sys
import unittest
import tempfile

from mocker import MockerTestCase, MATCH, CONTAINS

from zope import interface

from ore.contentmirror import schema
from ore.contentmirror.bulk import main as bulk
from ore.contentmirror.ddl import main as ddl
from ore.contentmirror.jsonschema import main as jsonschema

from base import IntegrationTestCase, SampleContent, CustomContent


class MockApp(object):

    results = []

    class Portal(object):

        class portal_catalog(object):

            @staticmethod
            def unrestrictedSearchResults(**kw):
                results = MockApp.results
                if 'portal_type' in kw:
                    query = kw['portal_type']
                    results = [r for r in results
                               if r.portal_type == query]
                if 'path' in kw:
                    query = kw['path']
                    results = [
                        r for r in results
                        if "/".join(r.getPhysicalPath()).startswith(query)]
                if 'modified' in kw:
                    query = kw['modified']
                    results = filter(
                        lambda x: getattr(x, 'modified', None), results)
                    results = [
                        r for r in results
                        if r.modified > query]
                return map(MockApp.Brain, results)

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


class ScriptTestCase(MockerTestCase, IntegrationTestCase):

    def _setup_args(self, *args):
        original_argv = list(sys.argv)
        sys.argv = list(args)

        def cleanup_args():
            sys.argv = original_argv
        self.addCleanup(cleanup_args)


class BulkScriptTest(ScriptTestCase):

    access_module_key = "AccessControl"
    manager_module_key = "AccessControl.SecurityManagement"
    cleanup_modules = False

    def setUp(self):
        super(BulkScriptTest, self).setUp()
        # setup a fake security module if we're running out
        # of a z2 environment.
        access_control = new.module(self.manager_module_key)
        security_manager = new.module(self.manager_module_key)
        security_manager.newSecurityManager = lambda x, y: None

        if not self.manager_module_key in sys.modules:
            sys.modules["AccessControl"] = access_control
            sys.modules[self.module_key] = security_manager

            def cleanup(self):
                del sys.modules[self.manager_module_key]
                del sys.modules[self.access_module_key]
            self.addCleanup(cleanup, self)

        snippet = """
        <ore:mirror content='%s'/>
        """ % (self.sample_content)
        self._load(snippet)
        schema.metadata.create_all()
        interface.classImplementsOnly(CustomContent, ())

    def tearDown(self):
        schema.metadata.drop_all(checkfirst=True)
        super(BulkScriptTest, self).tearDown()

    def testNoPortalPath(self):
        self._setup_args("")
        mock_exit = self.mocker.replace("sys.exit")
        mock_stdout = self.mocker.replace("sys.stdout")
        mock_stdout.write(CONTAINS("usage:"))
        mock_exit(1)
        self.mocker.result(None)
        self.mocker.replay()
        MockApp.results = []
        bulk(MockApp)

    def testBulk(self):
        self._setup_args("", "portal")
        c1 = SampleContent("a")
        # what happens when we don't have a uid for an object
        c2 = SampleContent("b")
        c2.uid = ""
        # what happens when we ddon't have a serializer for an
        # object
        c3 = CustomContent("c")

        # see what happens an exception gets raised fetching
        c4 = CustomContent("d")
        c4.UID = lambda: 1/0

        MockApp.results = [c1, c2, c3, c4]

        stdout_mock = self.mocker.replace("sys.stdout")
        stdout_mock.write(MATCH(TextMatch("Processed")))
        stdout_mock.write(MATCH(TextMatch("Processed")))
        stdout_mock.write(MATCH(TextMatch("Finished")))
        self.mocker.replay()
        bulk(MockApp, "portal", 1)


class TextMatch(object):

    def __init__(self, target):
        self.target = target

    def __call__(self, value):
        return self.target in value


class DDLScriptTest(ScriptTestCase):

    def test_ddl(self):
        self._setup_args("", "sqlite")
        stdout_mock = self.mocker.replace("sys.stdout")

        def match_output(output):
            return ("CREATE" in output) and ("DROP" not in output)

        stdout_mock.write(MATCH(match_output))
        stdout_mock.write("\n")
        self.mocker.replay()
        ddl()

    def test_drop_only(self):
        self._setup_args("", "-d", "-n", "sqlite")
        stdout_mock = self.mocker.replace("sys.stdout")

        def match_output(output):
            return ("CREATE" not in output) and ("DROP" in output)

        stdout_mock.write(MATCH(match_output))
        stdout_mock.write("\n")
        self.mocker.replay()
        ddl()

    def test_drop_and_create(self):
        self._setup_args("", "-d", "sqlite")
        stdout_mock = self.mocker.replace("sys.stdout")

        def match_output(output):
            return ("CREATE" in output) and ("DROP" in output)

        stdout_mock.write(MATCH(match_output))
        stdout_mock.write("\n")
        self.mocker.replay()
        ddl()


class JsonSchemaScriptTest(ScriptTestCase):

    def setUp(self):
        super(JsonSchemaScriptTest, self).setUp()
        snippet = """
        <ore:mirror content='%s'/>
        """ % (self.sample_content)
        self._load(snippet)

    def test_file_output(self):
        fh = tempfile.NamedTemporaryFile()
        self._setup_args("", fh.name)
        jsonschema()
        fh.flush()
        fh.seek(0)
        output = fh.read()
        self.assertTrue("stuff" in output)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
