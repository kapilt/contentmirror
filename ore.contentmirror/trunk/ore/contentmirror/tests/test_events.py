import unittest
import transaction

from zope.configuration.xmlconfig import XMLConfig
from zope.lifecycleevent import ObjectModifiedEvent
from zope import event
# plone <4
from zope.app.container.contained import ObjectAddedEvent, ObjectRemovedEvent

from ore import contentmirror
from ore.contentmirror import schema
from base import IntegrationTestCase, SampleContent

try:
    from Products.CMFCore.WorkflowCore import ActionSucceededEvent
except:
    ActionSucceededEvent = None


class EventSubcriberTest(IntegrationTestCase):

    def setUp(self):
        super(EventSubcriberTest, self).setUp()
        # plone 3 -> 4 incompatibility
        #XMLConfig("configure.zcml", component)() # plone 4
        import zope.app.event # side effect setups object events (plone3)
        XMLConfig("configure.zcml", zope.app.event)()
        XMLConfig("subscriber.zcml", contentmirror)()
        snippet = """
        <ore:mirror content='%s'/>
        """ % (self.sample_content)
        self._load(snippet)

    def test_delete_after_add_cancels_all(self):
        """
        Adding and deleting content results in no serialized content in the db.
        """
        instance = SampleContent("foobar")
        event.notify(ObjectAddedEvent(instance))
        event.notify(ObjectRemovedEvent(instance))
        transaction.commit()
        all = schema.content.select().execute()
        self.assertEqual(list(all), [])

    def test_modify_and_delete_cancels_all(self):
        """
        Creating content and then deleting it results in no content in the db.
        """
        instance = SampleContent("foobar")
        event.notify(ObjectModifiedEvent(instance))
        event.notify(ObjectRemovedEvent(instance))
        transaction.commit()
        all = schema.content.select().execute()
        self.assertEqual(list(all), [])

    def test_portal_factory_filter(self):
        """
        Content in portal factory never serializes.
        """
        request = SampleContent("request")
        portal = SampleContent("portal", container=request)
        container = SampleContent("portal_factory", container=portal)
        content = SampleContent("abc", container=container)

        event.notify(ObjectAddedEvent(content))
        transaction.commit()
        all = schema.content.select().execute()
        self.assertEqual(list(all), [])

    if ActionSucceededEvent:
        def testWorkflowEvent(self):
            pass


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
