import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from plone.models.search import Audit
from plone.models.base import Content
from plone.signals import on_update
from plone.signals import on_delete

from datetime import datetime

def fire_signals():
    if Audit.objects.count():
        timestamp = Audit.objects.get().timestamp
        query = Content.objects.filter(modified_date__gt=timestamp)
    else:
        query = Content.objects.all()

    for object in query:
        instance = object.content_object()
        on_update.send(None, instance=instance)

    if Audit.objects.count():
        audit = Audit.objects.get()
    else:
        audit = Audit()
        
    audit.timestamp = datetime.now()
    audit.save()
    
if __name__=="__main__":
    fire_signals()
