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
"""
The Model Loader drives the startup bootstrapping, its wired into the
zcml directives, its responsible for loading/generating the tables, 
and creating the rdb mapped peer classes.

"""
from zope import component
import schema, interfaces

class ModelLoader( object ):
    
    #def __init__( self ):
    #    self.store = component.getUtility( interfaces.IAppEngine, 'appengine')

    def load( self, klass ):
        instance = klass("transient")

        registry = component.queryUtility( interfaces.IPeerRegistry )
        if klass in registry:
            raise KeyError("Duplicate %r"%klass)

        transformer = self.transform( instance )
        peer_class = self.peer( instance, transformer )
        
        registry[ klass ] = peer_class
        
    def transform( self, instance ):
        store = component.getUtility( interfaces.IAppEngine, 'appengine')
        transformer = component.getMultiAdapter( (instance, store),
                                                interfaces.ISchemaTransformer )
        transformer.transform()
        return transformer
        
    def peer( self, instance, transformer ):
        factory = component.getMultiAdapter( ( instance, transformer ) ,
                                            interfaces.IPeerFactory )
        return factory.make()
        return object
        
loader = ModelLoader()
load = loader.load

   
