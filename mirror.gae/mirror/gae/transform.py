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

from zope import interface, component

from md5 import md5
from datetime import datetime
import interfaces, schema

class SchemaTransformer( object ):
    """
    the schema transformer is stateful and in memory persistent, its responsible for
    parsing the at schema and transforming it to a database table.  

    its also responsible for copying an object state from an instance to a peer.
    """
    interface.implements( interfaces.ISchemaTransformer )
    
    def __init__( self, context, store):
        self.context = context
        self.properties = {}
        
    def transform( self ):
        return
                                
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
        for field in self.context.Schema().fields():
            if not self.filter( field ):
                continue
                
            transformer = component.getMultiAdapter( ( field, self ))
            result = transformer.transform()
            
            if isinstance( result, "" ):
                yield result
                

class BaseFieldTransformer( object ):
    
    interface.implements( interfaces.IFieldTransformer )

    def __init__( self, context, transformer):
        self.context = context
        self.transformer = transformer

    def transform( self ):
        column = self.name
        self.transformer.properties[ self.name ] = column
        return column
    
    def copy( self, instance, peer ):
        accessor = self.context.getAccessor( instance )
        value = accessor()
        setattr( peer, self.name, value )
                                 
    @property                      
    def name( self ):
        name = self.context.__name__.lower()
        name = name.replace(' ', '_')
        return name
    
class ComputedTransform( BaseFieldTransformer):
    component.adapts( interfaces.IComputedField, interfaces.ISchemaTransformer)
    column_type = "text"
    column_args = ()
    
class StringTransform( BaseFieldTransformer ):    
    component.adapts( interfaces.IStringField, interfaces.ISchemaTransformer )
    column_type = "text"
    column_args = ()
    
    def copy( self, instance, peer ):
        accessor = self.context.getAccessor( instance )
        value = accessor()
        
        # one of a number of common bad practices that plone permits is specing a widget
        # which doesn't correspond to the field. ie. using a lines widget with a string field
        # actually generates a list value for the field. sadly this sort of sloppy usage appears
        # to be rather common place, so we'll try to handle it inline.. at least for now. 
        if isinstance( value, (tuple, list)):
            return LinesTransform( self.context, self.transformer ).copy( instance, peer )
        # at least morph it into a value which won't cause further issues.
        if not isinstance( value, basestring):
            value = str( value )
            
        setattr( peer, self.name, value )    

class TextTransform( BaseFieldTransformer ):    
    component.adapts( interfaces.IStringField, interfaces.ISchemaTransformer )
    column_type = "text"
    column_args = ()    
        
class LinesTransform( StringTransform ):    
    component.adapts( interfaces.ILinesField, interfaces.ISchemaTransformer )
    
    def copy( self, instance, peer ):
        accessor = self.context.getAccessor( instance )
        value = accessor()
        if isinstance(value, type("")):
            value = [value]
        if isinstance(value, tuple):
            value = list(value)
        setattr( peer, self.name, value )        
        
class FileTransform( object ):    
    """
    a file field serializer that utilizes a file peer.
    """
    interface.implements( interfaces.IFieldTransformer )
    component.adapts( interfaces.IFileField, interfaces.ISchemaTransformer )    

    def __init__( self, context, transformer ):
        self.context = context
        self.transformer = transformer
        
    def copy( self, instance, peer ):
        accessor = self.context.getAccessor( instance )
        value = accessor()
        if not value: return 
        setattr( peer, self.name, value)
        
class ImageTransform( FileTransform ):     
    component.adapts( interfaces.IImageField, interfaces.ISchemaTransformer )
    
class PhotoTransform( FileTransform ):     
    component.adapts( interfaces.IPhotoField, interfaces.ISchemaTransformer )    

class BooleanTransform( BaseFieldTransformer):    
    component.adapts( interfaces.IBooleanField, interfaces.ISchemaTransformer )
    column_type = "boolean"

class IntegerTransform( BaseFieldTransformer):
    component.adapts( interfaces.IIntegerField, interfaces.ISchemaTransformer )
    column_type = "int"
    
class FloatTransform( BaseFieldTransformer ):    
    component.adapts( interfaces.IFloatField, interfaces.ISchemaTransformer )
    column_type = "float"
    
class DateTimeTransform( BaseFieldTransformer ):
    column_type = "date"
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
        
    def copy( self, instance, peer ):
        value = self.context.getAccessor( instance )()

        single_value = not self.context.multiValued 
        
        if not value:
            return
        
        if not isinstance( value, (list, tuple)):
            value= [ value ]

        setattr( peer, self.name, value )
