import unittest
import transaction
import sqlalchemy as rdb
from ore.contentmirror.tests.base import (
    IntegrationTestCase, SampleContent, ReferenceField, StringField, Schema)
from ore.contentmirror import schema, interfaces, session


class SReferenceContent(SampleContent):

    portal_type = "Single Value Reference Content"
    schema = Schema((StringField("description"),
                     ReferenceField("article_text",
                                    relationship="article",
                                    multiValued=False),
                     ReferenceField("press_photo",
                                    relationship="photo",
                                    multiValued=False),
                     ))


class SingleValueReferenceTestCase(IntegrationTestCase):

    def setUp(self):
        super(SingleValueReferenceTestCase, self).setUp()
        klass = "ore.contentmirror.tests.test_references.SReferenceContent"
        self._load("<ore:mirror content='%s'/>"%(klass))

    def test_peer_schema(self):
        """
        Single value references generate a table schema with a foreign key to
        the content table, and a relation property on the peer.
        """
        table = schema.metadata.tables["sreferencecontent"]
        self.assertTrue(isinstance(table.c.article_text_id.type, rdb.Integer))
        self.assertEqual(table.c.article_text_id.foreign_keys[0]._colspec,
                         "content.content_id")
        self.assertTrue(isinstance(table.c.press_photo_id.type, rdb.Integer))
        self.assertEqual(table.c.press_photo_id.foreign_keys[0]._colspec,
                         "content.content_id")

    def test_reference_set_multivalue(self):
        """
        Setting a multi value on a single reference field, uses only the first
        value.
        """
        article = SReferenceContent("article")
        photo = SReferenceContent("photo")
        news_item = SReferenceContent(
            "news_item", article_text=[article, photo])
        peer = interfaces.ISerializer(news_item).add()
        self.assertEqual(peer.article_text.id, "article")

    def test_relation_reference(self):
        """
        The content reference is available via a relation on the peer.
        """
        article = SReferenceContent("article")
        photo = SReferenceContent("photo")
        news_item = SReferenceContent(
            "news_item", article_text=article, press_photo=photo)
        peer = interfaces.ISerializer(news_item).add()
        self.assertTrue(peer.press_photo.id == "photo")
        self.assertTrue(peer.article_text.id == "article")

    def test_reference_set_null(self):
        """Setting a reference to None, deletes the relation."""
        article = SReferenceContent("article")
        news_item = SReferenceContent("news_item", article_text=article)
        interfaces.ISerializer(news_item).add()
        session.Session().flush()
        news_item.article_text = None
        peer = interfaces.ISerializer(news_item).update()
        self.assertEqual(peer.article_text, None)

    def test_reference_delete_referenced(self):
        """Deleting the referenced content sets the refation to None."""
        article = SReferenceContent("article")
        news_item = SReferenceContent("news_item", article_text=article)
        interfaces.ISerializer(news_item).add()
        transaction.commit()
        interfaces.ISerializer(article).delete()
        transaction.commit()
        # Verify the reference is gone in the database, this relies
        # on the database having fk triggers though for the delete set
        # null which sqlite does not have, so we try to grab the
        # reference sqlalchemy will resolve to None.
        peer = schema.fromUID(news_item.UID())
        self.assertEqual(peer.article_text, None)

    def test_reference_delete_self(self):
        """Deleting the content doesn't cascade to the referenced content."""
        article = SReferenceContent("article")
        news_item = SReferenceContent("news_item", article_text=article)
        interfaces.ISerializer(news_item).add()
        transaction.commit()
        interfaces.ISerializer(news_item).delete()
        self.assertEqual(schema.fromUID(news_item.UID()), None)


class MultiValueReferenceTestCase(IntegrationTestCase):

    def test_reference_set_multivalue(self):
        pass


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
