"""
Plone Functional test for copy&paste, cut&paste, and rename.
"""

from unittest import defaultTestLoader

import transaction

from ore.contentmirror import schema
from ore.contentmirror.ptests.base import MirrorTestCase


class CopyPasteRemoveTest(MirrorTestCase):

    def _create_content(self, id):
        self.loginAsPortalOwner()
        self.portal.invokeFactory("Document", id)
        transaction.commit()
        self.assertEqual(len(list(schema.content.select().execute())), 1)
        return self.portal[id]

    def _create_tree(self, ids):
        self.loginAsPortalOwner()
        container_id = ids.pop(0)
        self.portal.invokeFactory("Folder", container_id)
        container = self.portal[container_id]
        for content_id in ids:
            container.invokeFactory("Document", content_id)
        transaction.commit()
        return container

    def _verify_path(self, path):
        query = schema.content.select().where(
            schema.content.c.relative_path == path)
        results = query.execute()
        return list(results)

    def test_cut_paste_content(self):
        document = self._create_content("content_abc")
        transaction.commit()
        cp = self.portal.manage_cutObjects([document.getId()])
        self.portal.invokeFactory("Folder", "cut_content")
        folder = self.portal["cut_content"]
        folder.manage_pasteObjects(cp)
        transaction.commit()
        # verify number of objects
        self.assertEqual(len(list(schema.content.select().execute())), 2)
        # verify path of moved content
        results = self._verify_path("cut_content/content_abc")
        self.assertEqual(len(results), 1)

    def test_cut_paste_container(self):
        container = self._create_tree(["folder_g", "doc_b"])
        transaction.commit()
        cp = self.portal.manage_cutObjects([container.getId()])
        self.portal.invokeFactory("Folder", "cut_content_2")
        folder = self.portal["cut_content_2"]
        folder.manage_pasteObjects(cp)
        transaction.commit()
        # verify number of objects
        self.assertEqual(len(list(schema.content.select().execute())), 3)
        # verify path of moved content
        results = self._verify_path("cut_content_2/folder_g/doc_b")
        self.assertEqual(len(results), 1)

    def test_copy_paste_content(self):
        document = self._create_content("content_xyz")
        cp = self.portal.manage_copyObjects([document.getId()])
        self.portal.manage_pasteObjects(cp)
        transaction.commit()
        # verify new content added
        self.assertEqual(len(list(schema.content.select().execute())), 2)
        # verify new content path
        self.assertEqual(len(self._verify_path("copy_of_content_xyz")), 1)

    def test_copy_paste_container(self):
        """
        Copy and Pasting a container in zope, does not automatically copy the
        content within it.
        """
        container = self._create_tree(["folder_b", "doc_b"])
        transaction.commit()
        cp = self.portal.manage_copyObjects([container.getId()])
        self.portal.manage_pasteObjects(cp)
        transaction.commit()
        self.assertEqual(self.portal.copy_of_folder_b.objectIds(), ["doc_b"])
        self.assertEqual(len(list(schema.content.select().execute())), 4)
        # verify new content path
        self.assertEqual(len(self._verify_path("copy_of_folder_b/doc_b")), 1)

    def test_clone_container(self):
        """
        Cloning doesn' change archetypes uid?
        """
        container = self._create_tree(["folder_c", "doc_c"])
        transaction.commit()
        self.portal.manage_clone(container, "folder_d")
        transaction.commit()
        self.assertEqual(len(list(schema.content.select().execute())), 4)
        self.assertEqual(self.portal.folder_d.objectIds(), ["doc_c"])
        # verify new content path
        self.assertEqual(len(self._verify_path("folder_d/doc_c")), 1)

    def test_rename(self):
        document = self._create_content("content_123")
        transaction.commit()
        self.portal.manage_renameObject(document.getId(), "content_111")
        transaction.commit()
        # verify number of objects
        self.assertEqual(len(list(schema.content.select().execute())), 1)
        # verify new path
        results = self._verify_path("content_111")
        self.assertEqual(len(results), 1)

    def test_rename_container(self):
        container = self._create_tree(["folder_e", "doc_e"])
        transaction.commit()
        self.portal.manage_renameObject(container.getId(), "folder_f")
        transaction.commit()
        # verify rename of contained content in db.
        self.assertEqual(self.portal.folder_f.objectIds(), ["doc_e"])
        results = self._verify_path("folder_f/doc_e")
        self.assertEqual(len(results), 1)


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)
