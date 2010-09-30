import new
import sys
import os
import unittest
import tempfile
import transaction

import sqlalchemy as rdb

from mocker import MockerTestCase, MATCH, CONTAINS

from zope import interface
from DateTime import DateTime

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
                    query = kw['path']['query']
                    res = []
                    for r in results:
                        path = "/".join(r.getPhysicalPath())
                        for qp in query:
                            if path.startswith(qp):
                                res.append(r)
                    results = res
                if 'modified' in kw:
                    query = kw['modified']['query']
                    results = filter(
                        lambda x: getattr(
                            x, 'modification_date', None), results)
                    results = [
                        r for r in results
                        if r.modification_date > query]
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
        transaction.abort()

    def _sample_content(self):
        a = SampleContent("a")
        b = SampleContent("b", a)
        c = SampleContent("c")
        d = SampleContent("e", b)
        return [a, b, c, d]

    def _fetch_rows(self):
        return list(schema.content.select().execute())

    def _capture_standard_output(self, replay=True):
        stdout_mock = self.mocker.replace("sys.stdout")
        stdout_mock.write(CONTAINS("Processed"))
        stdout_mock.write(CONTAINS("Finished"))
        if replay:
            self.mocker.replay()

    def test_acquire_app(self):
        """
        The script will attempt to acquire the app from the
        call stack so that its compatible with usage via
        ./bin/instance run ./bin/script
        """
        app = MockApp
        app.results = self._sample_content()
        self._setup_args("", "portal")
        self._capture_standard_output()
        bulk()

    def test_specify_database(self):
        """
        The database can be specified as a command line option.

        We need to first create the database schema in the given
        database.
        """
        db_path = self.makeFile(suffix="_mirror_test.db")
        # populate tables
        schema.metadata.bind = rdb.create_engine("sqlite:///%s"%db_path)
        schema.metadata.create_all()
        # reset engine
        schema.metadata.bind = None

        self._setup_args("", "-d", "sqlite:///%s"%db_path, "portal")
        self._capture_standard_output()
        MockApp.results = self._sample_content()
        bulk(MockApp)
        self.assertTrue(os.path.exists(db_path))
        self.assertTrue(os.path.getsize(db_path) > 1024)

    def test_sync_incremental(self):
        """
        Content can be sync'd incrementally based on the last
        timestamp of content in the db.
        """
        self._setup_args("", "--incremental", "portal")
        MockApp.results = content = self._sample_content()
        content[-1].modification_date = DateTime()
        # Mock output of both runs
        stdout_mock = self.mocker.replace("sys.stdout")
        stdout_mock.write(MATCH(TextMatch("Processed", '  4')))
        stdout_mock.write(MATCH(TextMatch("Finished")))
        # second run we'll only have two new objects
        stdout_mock.write(MATCH(TextMatch("Processed", '  2')))
        stdout_mock.write(CONTAINS("Finished"))
        self.mocker.replay()

        bulk(MockApp)
        self.assertEqual(len(self._fetch_rows()), len(content))
        new_content = SampleContent("e", content[-1])
        new_content.modification_date = DateTime()+2
        modified_content = content[0]
        modified_content.modification_date = DateTime()+1
        MockApp.results.append(new_content)
        bulk(MockApp)
        self.assertEqual(len(self._fetch_rows()), len(content))

    def test_path(self):
        """
        Content can be serialized only from a given path.
        """
        self._setup_args("", "--path", "c", "portal")
        MockApp.results = self._sample_content()
        stdout_mock = self.mocker.replace("sys.stdout")
        stdout_mock.write(MATCH(TextMatch("Processed", '  1')))
        stdout_mock.write(MATCH(TextMatch("Finished")))
        self.mocker.replay()
        bulk(MockApp)
        self.assertEqual(len(self._fetch_rows()), 1)

    def test_dump_types(self):
        """
        Content only of the given types (and their containers) can be specified
        for serialization.
        """
        content = self._sample_content()
        content[0].portal_type = "Folder"
        content[-1].portal_type = "Article"
        MockApp.results = content
        self._setup_args("", "--types", '"Folder, Article"', "portal")
        self._capture_standard_output()
        bulk(MockApp)

    def test_no_portal_path(self):
        """
        Not specifying a portal path results in an the script exit
        and the usage information.
        """
        self._setup_args("")
        mock_exit = self.mocker.replace("sys.exit")
        mock_stdout = self.mocker.replace("sys.stdout")
        mock_stdout.write(CONTAINS("usage:"))
        mock_exit(1)
        #self.mocker.result(None)
        self.mocker.replay()
        MockApp.results = []
        bulk(MockApp)

    def test_bulk(self):
        """
        Bulk serialization of all content is done by default.
        """
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

    def _snapshot_clean_environ(self):
        environ = dict(os.environ)

        def cleanup():
            os.environ.update(environ)
            old_keys = set(environ.keys())
            new_keys = set(os.environ.keys())
            for new_key in (new_keys - old_keys):
                del os.environ[new_key]
        self.addCleanup(cleanup)

    def test_db_from_environment(self):
        self._snapshot_clean_environ()
        db_path = self.makeFile(suffix="_mirror_test.db")
        os.environ["CONTENTMIRROR_URI"] = "sqlite:///%s"%db_path
        schema.environ_db()
        self.assertEqual(str(schema.metadata.bind.url),
                         "sqlite:///%s"%db_path)


class TextMatch(object):

    def __init__(self, *targets):
        self.targets = targets

    def __call__(self, value):
        for m in self.targets:
            if not m:
                continue
            m = str(m)
            if not m in value:
                return False
        return True


class DDLScriptTest(ScriptTestCase):

    def test_ddl(self):
        self._setup_args("", "sqlite")
        stdout_mock = self.mocker.replace("sys.stdout")

        def match_output(output):
            return ("CREATE" in output) and ("DROP" not in output)

        stdout_mock.write(MATCH(match_output))
        self.mocker.replay()
        ddl()

    def test_drop_only(self):
        self._setup_args("", "-d", "-n", "sqlite")
        stdout_mock = self.mocker.replace("sys.stdout")

        def match_output(output):
            return ("CREATE" not in output) and ("DROP" in output)

        stdout_mock.write(MATCH(match_output))
        self.mocker.replay()
        ddl()

    def test_drop_and_create(self):
        """
        Script can be configured to issue drop and then create table statements
        """
        self._setup_args("", "-d", "sqlite")
        stdout_mock = self.mocker.replace("sys.stdout")

        def match_output(output):
            return ("CREATE" in output) and ("DROP" in output)

        stdout_mock.write(MATCH(match_output))
        self.mocker.replay()
        ddl()

    def test_no_dialect_specified(self):
        """
        Not specifying a dialect results in the script exiting with a usage
        message.
        """
        self._setup_args("")
        mock_exit = self.mocker.replace("sys.exit")
        mock_stdout = self.mocker.replace("sys.stdout")
        mock_stdout.write(CONTAINS("usage:"))
        mock_exit(1)
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
