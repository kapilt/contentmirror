from django.db.models import signals
from django.db import connection

fix_columns_called = False

# this cleans up the relations to ensure that 
# there it is usable in django

sql = [
"""
ALTER TABLE relations DROP CONSTRAINT relations_pkey;
ALTER TABLE relations DROP CONSTRAINT relations_source_id_fkey;
ALTER TABLE relations DROP CONSTRAINT relations_target_id_fkey;
""","""
ALTER TABLE relations ADD COLUMN id serial not null;
ALTER TABLE relations ADD PRIMARY KEY (id);
CREATE INDEX "relations_source_id" ON "relations" ("source_id");
CREATE INDEX "relations_target_id" ON "relations" ("target_id");
""","""
ALTER TABLE content ADD COLUMN "signals_sent" timestamp with time zone;
"""]

def fix_columns(sender=None, **kw):
    global fix_columns_called
    if fix_columns_called:
        return
    cursor = connection.cursor()
    for statement in sql:
        cursor.execute(statement)
    fix_columns_called = True

signals.post_syncdb.connect(fix_columns)

# create some signals to clean up resolveuid
# and make links in documents actually work 
# this is a custom signal
from django.dispatch import Signal
from plone.models.base import Content

on_update = Signal(providing_args=["instance"])
on_delete = Signal(providing_args=["model", "content_type", "content_id"])

import re
IMG_SRC_PATTERN = re.compile('src\s*=\s*"(?P<src>([^"]*))', re.VERBOSE | re.IGNORECASE | re.DOTALL)

def set_text_display(sender=None, **kw):
    instance = kw.get("instance")
    if not hasattr(instance, "text"):
        return
    
    text = instance.text
    res = IMG_SRC_PATTERN.findall(text)
    repl = []
    for string in res:
        # the url could be resolve_uid/UID or resolve_uid/UID/image_small
        uid = string[0].split('/')[1]
        # look it up
        try:
            obj = Content.objects.get(uid=uid).content_object()
        except Content.DoesNotExist:
            continue
            
        if hasattr(obj, "get_download_url"):
            url = obj.get_download_url()
        else:
            url = obj.get_absolute_url()
        repl.append([string[0], url])

    if repl:
        # process all the replacements
        for orig, replacement in repl:
            text = text.replace(orig, replacement)

        instance.text = text
        instance.save()
    
on_update.connect(set_text_display)