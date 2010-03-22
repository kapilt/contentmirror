
from ore.contentmirror import interfaces
from zope import interface


class NullFieldTransform(object):
    interface.implements(interfaces.IFieldTransformer)

    def transform(self):
        return

    def copy(self, instance, peer):
        return
