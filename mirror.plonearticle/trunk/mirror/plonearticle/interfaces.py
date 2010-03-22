
from zope import interface


class IFileInnerContentField(interface.Interface):
    """Marker interface for File field"""


class IImageInnerContentField(interface.Interface):
    """Marker interface for Image field"""


class ILinkInnerContentField(interface.Interface):
    """Marker interface for Link field"""


class ISmartListField(interface.Interface):
    """Marker interface for Reference List field"""
