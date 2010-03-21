
import sqlalchemy
import transaction
from unittest import defaultTestLoader


from zope import interface, component, event
from zope.configuration.xmlconfig import XMLConfig
from zope.lifecycleevent import ObjectModifiedEvent
from zope.app.container.contained import ObjectAddedEvent, ObjectRemovedEvent

from ore import contentmirror
from ore.contentmirror import interfaces, schema

from base import IntegrationTest, SampleContent, CustomContent


def CustomSerializer(context):
    return 42


class CustomTransformer(object):
    interface.implements(interfaces.ISchemaTransformer)

    def __init__(self, context, metadata):
        self.table = None
        self.properties = {}

    def transform(self):
        pass


class ZCMLTest(IntegrationTest):

    def testMirror(self):
        snippet = """
        <ore:mirror content='%s'/>
        """ % (self.sample_content)
        self._load(snippet)
        content = SampleContent("sample")
        serializer = interfaces.ISerializer(content)
        self.assertTrue(serializer)

    def testNonMirrored(self):
        snippet = """
        <ore:mirror content='%s'/>
        """ % (self.custom_content)
        self._load(snippet)
        content = CustomContent("sample")
        serializer = interfaces.ISerializer(content)
        self.assertTrue(serializer)

    def testMirrorCustomSerializer(self):
        snippet = """\
        <ore:mirror content='%s' serializer="%s"/>
        """%(self.sample_content,
             "ore.contentmirror.tests.test_zcml.CustomSerializer")
        self._load(snippet)
        content = SampleContent("sample")
        serializer = interfaces.ISerializer(content)
        self.assertEqual(serializer, 42)

    def testMirrorCustomTransformer(self):
        snippet = """\
        <ore:mirror content='%s' transformer="%s"/>
        """%(self.sample_content,
             "ore.contentmirror.tests.test_zcml.CustomTransformer")
        self._load(snippet)
        content = SampleContent("sample")
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

        class CustomSub(SampleContent):
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
        #XMLConfig("configure.zcml", component)() # plone 4
        import zope.component.event # side effect setups object events (plone3)
        zope.component.event # pyflakes

        XMLConfig("subscriber.zcml", contentmirror)()
        self._load(snippet)
        instance = SampleContent("foobar")
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
        instance = SampleContent("bar", stuff=list("abc"))
        peer = interfaces.ISerializer(instance).add()
        self.assertEqual(peer.id, "bar")
        self.assertEqual(peer.stuff, "\n".join(list("abc")))

    def testOtherNonStringValue(self):
        snippet = """
        <ore:mirror content='%s'/>
        """ % (self.sample_content)
        self._load(snippet)
        instance = SampleContent("bar", stuff=CustomSerializer)
        peer = interfaces.ISerializer(instance).add()
        self.assertTrue(peer.stuff.startswith("<function"))


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)
