import unittest
import transaction
import sqlalchemy as rdb
from ore.contentmirror.tests.base import (
    IntegrationTestCase, SampleContent, BaseContent, ReferenceField,
    StringField, Schema)
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


class ReferenceContent(SampleContent):

    portal_type = "Reference Content"
    schema = Schema((StringField("description"),
                     ReferenceField("assets", relationship="article")))


class NonSerializable(BaseContent):

    portal_type = "Not Serialized"
    schema = Schema((StringField("description")))


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
        """Deleting the referenced content sets the relation to None."""
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

    def test_reference_multi_value_null(self):
        """
        Single value references only respect the first value if the reference
        contains multiple values, if the value is an empty list then no value
        is set.
        """
        news_item = SReferenceContent("news_item", article_text=[])
        interfaces.ISerializer(news_item).add()
        transaction.commit()
        peer = schema.fromUID(news_item.UID())
        self.assertEqual(peer.article_text, None)

    def test_reference_non_serializable_content(self):
        """
        If a reference is to content which is not serializable the
        reference is not set in the database.
        """
        article_text = NonSerializable("sample")
        news_item = SReferenceContent("news_Item", article_text=[article_text])
        interfaces.ISerializer(news_item).add()
        transaction.commit()
        peer = schema.fromUID(news_item.UID())
        self.assertEqual(peer.article_text, None)


class MultiValueReferenceTestCase(IntegrationTestCase):

    def setUp(self):
        super(MultiValueReferenceTestCase, self).setUp()
        klass = "ore.contentmirror.tests.test_references.ReferenceContent"
        self._load("<ore:mirror content='%s'/>"%(klass))
        schema.metadata.create_all(checkfirst=True)

    def test_reference_set_multivalue(self):
        """Multiple values for a reference can be set"""
        content_a = ReferenceContent("a")
        content_b = ReferenceContent("b")
        content_c = ReferenceContent("c", assets=[content_a, content_b])
        interfaces.ISerializer(content_c).add()
        transaction.commit()
        self.assertEqual(len(list(schema.content.select().execute())), 3)
        self.assertEqual(len(list(schema.relations.select().execute())), 2)

    def test_reference_modify_multivalue(self):
        """
        Setting a new value for a multivalue reference correctly updates
        the relations table to only the new value.
        """
        content_a = ReferenceContent("a")
        content_b = ReferenceContent("b")
        content_c = ReferenceContent("c", assets=[content_a, content_b])
        interfaces.ISerializer(content_c).add()
        transaction.commit()
        content_c.assets = [content_a]
        peer = interfaces.ISerializer(content_c).update()
        self.assertEqual(len(peer.relations), 2)

    def test_reference_non_serializable_content(self):
        """
        References to content which isn't serializable will ignore
        the reference.
        """
        content_a = NonSerializable("a")
        content_b = ReferenceContent("b")
        content_c = ReferenceContent("c", assets=[content_a, content_b])
        interfaces.ISerializer(content_c).add()
        transaction.commit()
        peer = schema.fromUID(content_c.UID())
        self.assertEqual(len(peer.relations), 1)

    def test_reference_delete_value(self):
        """
        Deleting a reference value content object removes it from the relations
        table.
        """
        content_a = ReferenceContent("a")
        content_b = ReferenceContent("b")
        content_c = ReferenceContent("c", assets=[content_a, content_b])
        interfaces.ISerializer(content_c).add()
        transaction.commit()
        interfaces.ISerializer(content_b).delete()
        peer = schema.fromUID(content_c.UID())
        self.assertEqual(len(list(schema.relations.select().execute())), 2)
        # sqlite won't cascade the deletes for us.
        if schema.metadata.bind.url.drivername != 'sqlite':
            self.assertEqual(len(peer.relations), 1)

    def test_reference_delete_self(self):
        """
        Deleting a content with references does not delete the associated
        reference content.
        """
        content_a = ReferenceContent("a")
        content_b = ReferenceContent("b")
        content_c = ReferenceContent("c", assets=[content_a, content_b])
        interfaces.ISerializer(content_c).add()
        transaction.commit()
        interfaces.ISerializer(content_c).delete()
        peer = schema.fromUID(content_b.UID())
        self.assertTrue(peer)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
