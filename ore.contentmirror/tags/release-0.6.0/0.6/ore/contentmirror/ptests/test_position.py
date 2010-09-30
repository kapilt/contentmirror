"""
Plone functional tests for serialization of container order
"""

from unittest import defaultTestLoader

import transaction
import sqlalchemy as rdb

from OFS.interfaces import IOrderedContainer

from ore.contentmirror import schema
from ore.contentmirror.ptests.base import MirrorTestCase


class ContainerPositionTest(MirrorTestCase):

    def setUp(self):
        super(ContainerPositionTest, self).setUp()
        self.loginAsPortalOwner()
        self.portal.invokeFactory("Folder", "sample")
        self.folder = self.portal["sample"]
        self.folder.invokeFactory("Document", "doc-a")
        self.folder.invokeFactory("Document", "doc-b")
        self.assertEqual(self.folder.objectIds(), ["doc-a", "doc-b"])
        transaction.commit()

    def _query_position(self, ids=("doc-a", "doc-b"), ids_only=True):
        fields = [schema.content.c.folder_position, schema.content.c.id]
        if ids_only:
            fields.pop(0)
        query = rdb.select(fields).where(
            schema.content.c.id.in_(ids)).order_by(
            schema.content.c.folder_position)
        results = list(query.execute())
        if ids_only:
            return [r[0] for r in results]
        return results

    def test_ordered_container_interface(self):
        """Verify the OrderedContainer interface being used."""
        self.assertTrue(IOrderedContainer.providedBy(self.folder))

    def test_move_content_up(self):
        """Moving content in a container is serialized to the db."""
        self.folder.moveObjectsUp(["doc-b"])
        self.assertEqual(self.folder.objectIds(), ["doc-b", "doc-a"])
        self.folder.plone_utils.reindexOnReorder(self.folder)
        transaction.commit()
        results = self._query_position()
        self.assertEqual(results, [u'doc-b', u'doc-a'])

    def test_move_content_down(self):
        """Moving content in a container is serialized to the db."""
        self.folder.moveObjectsDown(["doc-a"])
        self.assertEqual(self.folder.objectIds(), ["doc-b", "doc-a"])
        # plone's ui does this after all moves to update the catalog
        self.folder.plone_utils.reindexOnReorder(self.folder)
        transaction.commit()
        results = self._query_position()
        self.assertEqual(results, [u'doc-b', u'doc-a'])

    def test_portal_move_content_down(self):
        """
        we have to utilize an additional operation factory and serializer
        for the portal root since its not serializable.
        """
        self.portal.invokeFactory("Document", "doc-c")
        self.assertEqual(self.portal.objectIds()[-1], "doc-c")
        transaction.commit()# serialize the content
        self.portal.moveObjectsToTop(["doc-c"])
        self.portal.plone_utils.reindexOnReorder(self.portal)
        transaction.commit()
        results = self._query_position(ids=("doc-c",), ids_only=False)
        # it moves to the top of the content in the portal
        self.assertEqual(results, [(59, u"doc-c")])
        self.assertEquals(self.portal.contentIds()[0], "doc-c")


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)
