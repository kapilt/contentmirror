"""
Plone Functional test for copy&paste, cut&paste, and rename.
"""

from unittest import defaultTestLoader

import transaction

from ore.contentmirror.tests.base import reset_db
from ore.contentmirror.ptests.base import MirrorTestCase
from ore.contentmirror import schema


class CopyPasteRemoveTest(MirrorTestCase):

    def setUp(self):
        super(MirrorTestCase, self).setUp()
        reset_db()

    def _create_content(self, id):
        self.loginAsPortalOwner()
        self.portal.invokeFactory("Document", id)
        self.flush() # flush the op buffer
        self.assertEqual(len(list(schema.content.select().execute())), 1)
        return self.portal[id]

    def test_cut_paste_content(self):
        document = self._create_content("content_abc")
        transaction.commit()
        cp = self.portal.manage_cutObjects([document.getId()])
        self.portal.invokeFactory("Folder", "cut_content")
        folder = self.portal["cut_content"]
        folder.manage_pasteObjects(cp)
        self.flush()
        self.assertEqual(len(list(schema.content.select().execute())), 2)

    def test_copy_paste_content(self):
        document = self._create_content("content_xyz")
        cp = self.portal.manage_copyObjects([document.getId()])
        self.portal.manage_pasteObjects(cp)
        self.flush()
        self.assertEqual(len(list(schema.content.select().execute())), 2)

    def test_rename(self):
        document = self._create_content("content_123")
        transaction.commit()
        self.portal.manage_renameObject(document.getId(), "content_111")
        self.flush()
        self.assertEqual(len(list(schema.content.select().execute())), 1)


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)
