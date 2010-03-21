####################################################################
# Copyright (c) Kapil Thangavelu. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
####################################################################

"""
$Id: $
"""

import unittest
import sys
import new
from cStringIO import StringIO

import sqlalchemy
import transaction

from zope.configuration.xmlconfig import xmlconfig, XMLConfig
from zope.component.tests import clearZCML
from zope import component, interface, event
from zope.lifecycleevent import ObjectModifiedEvent
from zope.app.container.contained import ObjectAddedEvent, ObjectRemovedEvent

from zope.testing import doctest

from ore import contentmirror

import testing
import interfaces
import schema


def CustomSerializer(context):
    return 42


class CustomTransformer(object):
    interface.implements(interfaces.ISchemaTransformer)

    def __init__(self, context, metadata):
        self.table = None
        self.properties = {}

    def transform(self):
        pass


class CustomContent(object):
    schema = testing.Schema(())

    def __init__(self, id):
        pass

    def Schema(self):
        return self.schema

    def UID(self):
        return "21"


class FunctionalTest(unittest.TestCase):

    sample_content = "ore.contentmirror.testing.SampleContent"

    def setUp(self):
        testing.setUp(self)
        XMLConfig("meta.zcml", component)()
        XMLConfig("meta.zcml", contentmirror)()
        XMLConfig("base.zcml", contentmirror)()
        schema.metadata.bind = sqlalchemy.create_engine("sqlite://")
        schema.metadata.create_all()

    def tearDown(self):
        testing.tearDown(self)
        clearZCML()
        schema.metadata.drop_all(checkfirst=True)

    def _load(self, text):
        template = """\
        <configure xmlns='http://namespaces.zope.org/zope'
                   xmlns:ore='http://namespaces.objectrealms.net/mirror'
                   i18n_domain='mirror'>
        %s
        </configure>"""
        xmlconfig(StringIO(template % text))


class ZCMLTest(FunctionalTest):

    def testMirror(self):
        snippet = """
        <ore:mirror content='%s'/>
        """ % (self.sample_content)
        self._load(snippet)
        content = testing.SampleContent("sample")
        serializer = interfaces.ISerializer(content)
        self.assertTrue(serializer)

    def testNonMirrored(self):
        snippet = """
        <ore:mirror content='%s'/>
        """ % ("ore.contentmirror.tests.CustomContent")
        self._load(snippet)
        content = CustomContent("sample")
        serializer = interfaces.ISerializer(content)
        self.assertTrue(serializer)

    def testMirrorCustomSerializer(self):
        snippet = """\
        <ore:mirror content='%s' serializer="%s"/>
        """%(self.sample_content, "ore.contentmirror.tests.CustomSerializer")
        self._load(snippet)
        content = testing.SampleContent("sample")
        serializer = interfaces.ISerializer(content)
        self.assertEqual(serializer, 42)

    def testMirrorCustomTransformer(self):
        snippet = """\
        <ore:mirror content='%s' transformer="%s"/>
        """%(self.sample_content, "ore.contentmirror.tests.CustomTransformer")
        self._load(snippet)
        content = testing.SampleContent("sample")
        metadata = sqlalchemy.MetaData()
        transformer = component.getMultiAdapter((content, metadata),
                                                interfaces.ISchemaTransformer)
        self.assertTrue(isinstance(transformer, CustomTransformer))

    def testBind(self):
        engine = sqlalchemy.create_engine("sqlite://")
        interface.directlyProvides(engine, (interfaces.IDatabaseEngine))
        component.provideUtility(engine, name="sample")
        snippet = """\
        <ore:bind engine='sample'
                  metadata='ore.contentmirror.schema.metadata'/>"""
        self._load(snippet)
        self.assertEqual(schema.metadata.bind, engine)

    def testEngine(self):
        snippet = """\
        <ore:engine name='sample'
                    url='sqlite://'
                    echo='true'
                    strategy='threadlocal'/>
                    """
        self._load(snippet)
        db = component.getUtility(interfaces.IDatabaseEngine, name="sample")
        self.assertTrue(db)

    def testSubclass(self):

        class CustomSub(testing.SampleContent):
            pass

        snippet = """
        <ore:mirror content='%s'/>
        """ % (self.sample_content)
        self._load(snippet)
        registry = component.getUtility(interfaces.IPeerRegistry)
        factory = registry[CustomSub]
        self.assertTrue(factory)

    def testEventSubscribers(self):
        snippet = """
        <ore:mirror content='%s'/>
        """ % (self.sample_content)
        # plone 3 -> 4 incompatibility
        #XMLConfig("configure.zcml", component)()
        import zope.component.event # side effect setups object events

        XMLConfig("subscriber.zcml", contentmirror)()
        self._load(snippet)
        instance = testing.SampleContent("foobar")
        event.notify(ObjectAddedEvent(instance))
        event.notify(ObjectModifiedEvent(instance))
        event.notify(ObjectRemovedEvent(instance))
        transaction.commit()
        all = schema.content.select().execute()
        self.assertEqual(list(all), [])

    def testListNonStringValue(self):
        snippet = """
        <ore:mirror content='%s'/>
        """ % (self.sample_content)
        self._load(snippet)
        instance = testing.SampleContent("bar", stuff=list("abc"))
        peer = interfaces.ISerializer(instance).add()
        self.assertEqual(peer.id, "bar")
        self.assertEqual(peer.stuff, "\n".join(list("abc")))

    def testOtherNonStringValue(self):
        snippet = """
        <ore:mirror content='%s'/>
        """ % (self.sample_content)
        self._load(snippet)
        instance = testing.SampleContent("bar", stuff=CustomSerializer)
        peer = interfaces.ISerializer(instance).add()
        self.assertTrue(peer.stuff.startswith("<function"))


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


class BulkScriptTest(FunctionalTest):

    module_key = "AccessControl.SecurityManagement"
    cleanup_modules = False

    def setUp(self):
        schema.metadata.create_all()
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
        interface.classImplementsOnly(CustomContent, ())

    def tearDown(self):
        schema.metadata.drop_all(checkfirst=True)
        if self.cleanup_modules:
            del sys.modules[self.module_key]
            del sys.modules["AccessControl"]
        super(BulkScriptTest, self).tearDown()

    def testBulk(self):
        c1 = testing.SampleContent("a")
        c2 = testing.SampleContent("b")
        c2.uid = ""
        c3 = CustomContent("c")
        MockApp.results = [c1, c2, c3]
        from ore.contentmirror.bulk import main
        main(MockApp, "portal", 1)


class DDLScriptTest(FunctionalTest):
    pass


class JsonSchemaScriptTest(FunctionalTest):
    pass


def test_suite():

    return unittest.TestSuite((
        doctest.DocFileSuite(
            'readme.txt',
            setUp=testing.setUp, tearDown=testing.tearDown,
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
            globs=testing.doctest_ns),
        doctest.DocFileSuite(
            'ref.txt',
            setUp=testing.setUp, tearDown=testing.tearDown,
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
            globs=testing.doctest_ns),
        unittest.TestLoader().loadTestsFromTestCase((ZCMLTest)),
        #unittest.TestLoader().loadTestsFromTestCase((BulkScriptTest)),
    ))
