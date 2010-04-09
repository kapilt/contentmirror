"""
Some of plone products (including those form zope skel) will attempt to utilize
utilities that edepend on either acquisition or a local site before they've
been attached to the object graph. In order to cope when this when loading the
classes, we can either push and pop a local component manager with the required
local utilities. Or we can push and pop the utility directly to the class,
doing the latter is signficantly simpler and avoids having depending on
mimetypes tool in the test or runtime environment. More importantly it makes
much easier to maintain compatibility between mulitple plone versions.
"""


class MimeType(object):
    mime_type = "text/plain"
    binary = 0

    def __str__(self):
        return self.mime_type


class MimeTool(object):

    mime_type = MimeType()

    def __call__(self, data, **kw):
        return unicode(data), '', self.mime_type

    def guess_encoding(self, data):
        return "utf-8"

    def lookup(self, data):
        return [self.mime_type]

mimetypes_registry = MimeTool()


def push(cls):
    setattr(cls, "mimetypes_registry", mimetypes_registry)


def pop(cls):
    delattr(cls, "mimetypes_registry")
