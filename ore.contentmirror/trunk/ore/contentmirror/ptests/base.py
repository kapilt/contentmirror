from unittest import TestSuite, makeSuite

from Testing.ZopeTestCase import Sandboxed
from Products.PloneTestCase import PloneTestCase
from ore.contentmirror.ptests.layer import MirrorLayer
from ore.contentmirror.operation import get_buffer

PloneTestCase.setupPloneSite()

class MirrorTestCase(Sandboxed, PloneTestCase.PloneTestCase):

    layer = MirrorLayer

    events = ()

    def flush(self):
        get_buffer().flush()

    def capture_events(self):
        from zope.event import subscribers
        self.events = []
        subscribers.append(self._capture_events)

    def _capture_events(self, evt):
        self.events.append(evt)

    def cleanup_event_watcher(self):
        if self._capture_events in zope.event.subscribers:
            zope.event.subscribers.remove(self._capture_events)
            self.events = ()
