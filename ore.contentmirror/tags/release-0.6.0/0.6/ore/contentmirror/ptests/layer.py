from Products.PloneTestCase.layer import PloneSite
from Products.Five import zcml

from sqlalchemy import create_engine

from ore.contentmirror.tests.base import reset_db, test_db_uri


class MirrorLayer(PloneSite):

    @classmethod
    def setUp(cls):
        from ore.contentmirror import ptests, schema
        zcml.load_config("testing.zcml", ptests)
        schema.metadata.bind = create_engine(test_db_uri())
        schema.metadata.create_all()

    @classmethod
    def tearDown(cls):
        reset_db()
