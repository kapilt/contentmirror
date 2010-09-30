import traceback
from StringIO import StringIO

from Testing.ZopeTestCase import Sandboxed
from Products.PloneTestCase import PloneTestCase

from ore.contentmirror.ptests.layer import MirrorLayer
from ore.contentmirror.tests.base import reset_db
from ore.contentmirror.operation import get_buffer

PloneTestCase.setupPloneSite()


class MirrorTestCase(Sandboxed, PloneTestCase.PloneTestCase):

    layer = MirrorLayer

    events = ()

    _cleanup_funcs = ()

    def setUp(self):
        super(MirrorTestCase, self).setUp()
        reset_db()

    def tearDown(self):
        super(MirrorTestCase, self).tearDown()

        for cleanup, args, kw in self._cleanup_funcs:
            cleanup(*args, **kw)

    def addCleanup(self, func, *args, **kw):
        if not self._cleanup_funcs:
            self._cleanup_funcs = []
        self._cleanup_funcs.append((func, args, kw))

    def flush(self):
        get_buffer().flush()

    def capture_events(self):
        events = []

        def capture(evt):
            stack_trace = StringIO()
            traceback.print_stack(limit=30, file=stack_trace)
            events.append((evt, stack_trace))

        from zope import event
        event.subscribers.append(capture)

        self.addCleanup(event.subscribers.remove, capture)
        return events

    def pprint_events(self, events_capture):

        print "Events Capture and Traces"
        for event, trace in events_capture:
            print event
            print trace.getvalue()
            print
