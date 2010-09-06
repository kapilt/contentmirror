"""
Plone Environment Construction for Transient Content Creation.

Some of plone products (including those from zope skel) will attempt to utilize
utilities that depend on either acquisition or a local site before they've
been attached to the object graph. In order to cope when this when loading the
classes, we can either push and pop a local component manager with the required
local utilities. Or we can push and pop the utility directly to the class,
doing the latter is signficantly simpler and avoids having depending on
mimetypes tool in the test or runtime environment. More importantly it makes
it much easier to maintain compatibility between mulitple plone versions and
the underlying differences in the component architecture with the resulting
zope versions.
"""

import sys
from zope.event import notify
from ore.contentmirror.interfaces import ContainerOrderChanged


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


def reindexOnReorder(self, parent):
    """
    In order to serialize content order in the container we need to modify
    plone in order to generate an event specific this to state change.

    Move events also generate a reindex, but this is effectively a
    redundant operation as the content doesn't change position. We attempt
    to filter these out here.
    """
    self._reindexOnReorder(parent)
    if sys._getframe(1).f_code.co_name != "manage_renameObject":
        notify(ContainerOrderChanged(parent))


def patch_plone():
    try:
        from Products.CMFPlone.PloneTool import PloneTool
    except ImportError:
        return

    PloneTool._reindexOnReorder = PloneTool.reindexOnReorder
    PloneTool.reindexOnReorder = reindexOnReorder

patch_plone()
