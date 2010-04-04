"""
Plone Functional test for copy, paste and rename.
"""

from unittest import defaultTestLoader

import transaction

from ore.contentmirror.ptests.base import MirrorTestCase
from ore.contentmirror import schema


class CopyPasteRemoveTest(MirrorTestCase):

    def _create_content(self, id):
        schema.metadata.create_all()
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


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)
