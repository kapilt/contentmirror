from unittest import TestSuite, makeSuite

from Testing.ZopeTestCase import Sandboxed
from Products.PloneTestCase import PloneTestCase
from ore.contentmirror.ptests.layer import MirrorLayer
from ore.contentmirror.operation import get_buffer

PloneTestCase.setupPloneSite()

class MirrorTestCase(Sandboxed, PloneTestCase.PloneTestCase):

    layer = MirrorLayer

    def flush(self):
        get_buffer().flush()
