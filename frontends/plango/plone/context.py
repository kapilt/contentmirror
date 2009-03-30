from plone.models.base import Folder

def add(self, *args, **kw):
    res = {
        "top_folders": Folder.objects.filter(container=None, status="published"),
    }
    return res