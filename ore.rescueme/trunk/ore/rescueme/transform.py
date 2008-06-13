####################################################################
# Copyright (c) Kapil Thangavelu. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
####################################################################

from sqlalchemy import orm
import sqlalchemy as rdb
from zope import interface, component

from datetime import datetime
from ore.alchemist import Session
from ore.rescueme import interfaces, schema

class SchemaTransformer( object ):
    """
    the schema transformer is stateful and in memory persistent, its responsible for
    parsing the at schema and transforming it to a database table.  

    its also responsible for copying an object state from an instance to a peer.
    """
    interface.implements( interfaces.ISchemaTransformer )
    
    def __init__( self, context, metadata):
        self.context = context
        self.metadata = metadata
        self.table = None
        self.properties = {}
        
    def transform( self ):
        columns = list(self.columns())
        self.table = rdb.Table( self.name,
                                self.metadata,
                                useexisting=True,
                                *columns )
        return self.table
                                
    def copy( self, instance, peer ):
        for field in self.context.Schema().fields():
            transformer = component.queryMultiAdapter( ( field, self ))
            transformer.copy( instance, peer )

    @property
    def name( self ):
        return self.context.__class__.__name__.lower().replace(' ', '_')        
        
    def filter( self, field ):
        # return false if filter, true if ok, filter dublin core
        return not field.__name__ in interfaces.DUBLIN_CORE

    def columns( self):
        
        yield rdb.Column( "content_id", 
                          rdb.Integer, 
                          rdb.ForeignKey('content.content_id', ondelete="CASCADE"), 
                          primary_key=True )

        for field in self.context.Schema().fields():
            if not self.filter( field ):
                continue
                
            transformer = component.getMultiAdapter( ( field, self ))
            result = transformer.transform()
            
            if isinstance( result, rdb.Column ):
                yield result
                

class BaseFieldTransformer( object ):
    
    interface.implements( interfaces.IFieldTransformer )

    column_type = rdb.String
    column_args = ()
    
    def __init__( self, context, transformer):
        self.context = context
        self.transformer = transformer

    def transform( self ):
        args, kw = self._extractDefaults()
        
        return rdb.Column( self.name, 
                           self.column_type( *self.column_args ),  
                           *args,
                           **kw )

    def copy( self, instance, peer ):
        accessor = self.context.getAccessor( instance )
        value = accessor()
        setattr( peer, self.name, value )
                                 
    @property                      
    def name( self ):
        name = self.context.__name__.lower()
        if name in interfaces.RESTRICTED:
            name = "at_" + name.lower()
        return name.replace(' ', '_')
        
    def _extractDefaults( self ):
        args = []

        #if use_field_default and field.default:
        #    args.append( rdb.PassiveDefault( field.default ) )
        kwargs = {
            'nullable' : not self.context.required,
            'key' : self.context.getName(),            
            }
        return args, kwargs        
        
class StringTransform( BaseFieldTransformer ):    
    component.adapts( interfaces.IStringField, interfaces.ISchemaTransformer )
    column_type = rdb.Text
    column_args = ()

class TextTransform( BaseFieldTransformer ):    
    component.adapts( interfaces.IStringField, interfaces.ISchemaTransformer )
    column_type = rdb.UnicodeText
    column_args = ()    

class LinesTransform( StringTransform ):    
    component.adapts( interfaces.ILinesField, interfaces.ISchemaTransformer )
    
    def copy( self, instance, peer ):
        accessor = self.context.getAccessor( instance )
        value = accessor()
        if isinstance(value, (list, tuple)):
            value = "\n".join(value)
        setattr( peer, self.name, value )        
    
class FileTransform( BaseFieldTransformer ):    
    component.adapts( interfaces.IFileField, interfaces.ISchemaTransformer )    
    column_type = rdb.Binary

class ImageTransform( FileTransform ):     
    component.adapts( interfaces.IImageField, interfaces.ISchemaTransformer )
    
class PhotoTransform( FileTransform ):     
    component.adapts( interfaces.IPhotoField, interfaces.ISchemaTransformer )    

class BooleanTransform( BaseFieldTransformer):    
    component.adapts( interfaces.IBooleanField, interfaces.ISchemaTransformer )
    column_type = rdb.Boolean

class IntegerTransform( BaseFieldTransformer):
    component.adapts( interfaces.IIntegerField, interfaces.ISchemaTransformer )
    column_type = rdb.Integer
    
class FloatTransform( BaseFieldTransformer ):    
    component.adapts( interfaces.IFloatField, interfaces.ISchemaTransformer )
    column_type = rdb.Float
    
class DateTimeTransform( BaseFieldTransformer ):
    column_type = rdb.DateTime
    component.adapts( interfaces.IDateTimeField, interfaces.ISchemaTransformer )

    def copy( self, instance, peer ):
        value = self.context.getAccessor( instance ) ()
        if not value:
            return
        value = datetime.fromtimestamp( value.timeTime() )
        setattr( peer, self.name, value )
        
        
class ReferenceTransform( object ):
    
    component.adapts( interfaces.IReferenceField, interfaces.ISchemaTransformer )
    interface.implements( interfaces.IReferenceField )
    
    def __init__( self, context, transformer):
        self.context = context
        self.transformer = transformer
        
    def transform( self ):
        return
        
    def copy( self, instance, peer ):
        value = self.context.getAccessor( instance )()

        if not value:
            return
        
        if not isinstance( value, (list, tuple)):
            value= [ value ]
        
        session = Session()
        for ob in value:
            peer_ob = schema.fromUID( ob.UID() )
            if peer_ob is None:
                serializer = interfaces.ISerializer( ob, None )
                if serializer is None: continue
                peer_ob = serializer.add()

            relation = schema.Relation( peer,
                                        peer_ob,
                                        self.context.relationship )
            session.save( relation )
