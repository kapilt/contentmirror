import sqlalchemy as rdb

from zope import component

from ore.contentmirror.transform import BaseFieldTransformer
from ore.contentmirror.interfaces import ISchemaTransformer

from mirror.pfg import interfaces

class TALESStringTransform( BaseFieldTransformer ):
    component.adapts( interfaces.ITALESStringField, ISchemaTransformer )
    column_type = rdb.Text
    column_args = ()
