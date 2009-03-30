
from django.db import models
from django.contrib import admin

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import connection
from plone.signals import on_update, on_delete

from django.utils.encoding import smart_unicode

# from http://www.djangosnippets.org/snippets/1328/
class VectorField (models.Field):
    def __init__(self, *args, **kwargs):
        kwargs['null'] = True
        kwargs['editable'] = False
        kwargs['serialize'] = False
        super(VectorField, self).__init__(*args, **kwargs)

    def db_type( self ):
        return 'tsvector'

class Search(models.Model):
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType)
    content_object = generic.GenericForeignKey()

    index = VectorField()

    class Meta:
        app_label = "plone"

    @staticmethod
    def query(query):
        query = connection.ops.quote_name(query)
        result = Search.objects.extra(where=["index @@ plainto_tsquery(%s)"], params=[query,])
        return result

# bits from http://www.arnebrodowski.de/blog/add-full-text-search-to-your-django-project-with-whoosh.html
def update_index(sender=None, **kw):
    catalog = 'pg_catalog.english'
    instance = kw.get("instance")

    data = [ smart_unicode(f) for f in instance.get_search_fields() if f ]
    data = " ".join(data)

    content_type = ContentType.objects.get_for_model(instance)

    if hasattr(instance, "content_id"):
        id = instance.content_id
    else:
        id = instance.id
    try:
        search = Search.objects.get(content_type__pk=content_type.id, object_id=id)
    except Search.DoesNotExist:
        search = Search.objects.create(content_object=instance)
        search.save()

    cursor = connection.cursor()
    sql = "update plone_search set index = to_tsvector(%s, %s) where id = %s"
    cursor.execute(sql, (catalog, data, search.id))
    cursor.execute("COMMIT;")
    cursor.close()

def delete_index(**kw):
    try:
        search = Search.objects.get(content_type__pk=kw["content_type"].id, object_id=kw["content_id"])
        search.delete()
    except Search.DoesNotExist:
        pass

# a quick way to keep track of changes
class Audit(models.Model):
    timestamp = models.DateTimeField()
    
    class Meta:
        app_label = "plone"        
        
on_update.connect(update_index)
on_delete.connect(delete_index)