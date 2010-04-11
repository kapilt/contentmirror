from Testing.ZopeTestCase import Sandboxed
from Products.PloneTestCase import PloneTestCase

from ore.contentmirror.ptests.layer import MirrorLayer
from ore.contentmirror.tests.base import reset_db
from ore.contentmirror.operation import get_buffer

PloneTestCase.setupPloneSite()


class MirrorTestCase(Sandboxed, PloneTestCase.PloneTestCase):

    layer = MirrorLayer

    events = ()

    def setUp(self):
        super(MirrorTestCase, self).setUp()
        reset_db()

    def flush(self):
        get_buffer().flush()
