import unittest

from zope.configuration.xmlconfig import XMLConfig
from zope.lifecycleevent import ObjectModifiedEvent
from zope import event
# plone <4
from zope.app.container.contained import (
    ObjectAddedEvent, ObjectRemovedEvent, ObjectMovedEvent)

from ore import contentmirror
from ore.contentmirror import operation
from base import IntegrationTestCase, SampleContent


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

    def test_add_generates_add_operation(self):
        """
        An object created event generates an add operation.
        """
        instance = SampleContent("foobar")
        event.notify(ObjectAddedEvent(instance))
        ops = operation.get_buffer().ops.values()
        self.assertEqual(len(ops), 1)
        content_operation = ops[0]
        self.assertTrue(
            isinstance(content_operation, operation.AddOperation))

    def test_delete_generates_delete_operation(self):
        """
        An object deleted event generates a delete operation.
        """
        instance = SampleContent("foobar")
        event.notify(ObjectRemovedEvent(instance))
        ops = operation.get_buffer().ops.values()
        self.assertEqual(len(ops), 1)
        content_operation = ops[0]
        self.assertTrue(
            isinstance(content_operation, operation.DeleteOperation))

    def test_move_generates_move_operation(self):
        """
        An object moved event generates a move operation.
        """
        instance = SampleContent("foobar")
        event.notify(ObjectMovedEvent(instance, None, None, None, None))
        ops = operation.get_buffer().ops.values()
        self.assertEqual(len(ops), 1)
        content_operation = ops[0]
        self.assertTrue(
            isinstance(content_operation, operation.MoveOperation))

    def test_modify_generates_update_operation(self):
        """
        A modification event results in an update operation.
        """
        instance = SampleContent("foobar")
        event.notify(ObjectModifiedEvent(instance))
        ops = operation.get_buffer().ops.values()
        self.assertEqual(len(ops), 1)
        content_operation = ops[0]
        self.assertTrue(
            isinstance(content_operation, operation.UpdateOperation))

    def test_delete_after_add_cancels_all(self):
        """
        Adding and deleting content results in no serialized content in the db.
        """
        instance = SampleContent("foobar")
        event.notify(ObjectAddedEvent(instance))
        event.notify(ObjectRemovedEvent(instance))
        ops = operation.get_buffer().ops.values()
        self.assertEqual(len(ops), 0)

    def test_modify_and_delete_results_in_delete(self):
        """
        Creating content and then deleting it results in no content in the db.
        """
        instance = SampleContent("foobar")
        event.notify(ObjectModifiedEvent(instance))
        event.notify(ObjectRemovedEvent(instance))
        ops = operation.get_buffer().ops.values()
        self.assertEqual(len(ops), 1)
        self.assertTrue(
            isinstance(ops[0], operation.DeleteOperation))

    def test_portal_factory_filter(self):
        """
        Content in portal factory never serializes.
        """
        request = SampleContent("request")
        portal = SampleContent("portal", container=request)
        container = SampleContent("portal_factory", container=portal)
        content = SampleContent("abc", container=container)

        event.notify(ObjectAddedEvent(content))
        ops = operation.get_buffer().ops.values()
        self.assertEqual(len(ops), 0)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
