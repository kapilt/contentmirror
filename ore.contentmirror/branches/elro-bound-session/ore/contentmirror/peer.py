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
from zope import interface

from ore.contentmirror import schema, interfaces

class PeerFactory( object ):
    
    interface.implements( interfaces.IPeerFactory )
    
    def __init__( self, context, transformer ):
        self.context = context
        self.transformer = transformer
        
    @property
    def name(self):
        return self.context.__class__.__name__ + 'Peer'
        
    def make( self ):
        klass = type( self.name, (schema.Content,),
                      dict(transformer=self.transformer) )

        orm.mapper( klass, 
                    self.transformer.table,
                    properties=dict(self.transformer.properties),
                    inherits=schema.Content,
                    polymorphic_on=schema.content.c.type,
                    polymorphic_identity=self.name )
        return klass
        
class PeerRegistry( object ):
    
    interface.implements( interfaces.IPeerRegistry )
    
    def __init__( self ):
        self._peer_classes = {}
        
    def __setitem__( self, key, value ):
        self._peer_classes[ key ] = value        
        
    def __getitem__( self, key ):
        return self._peer_classes[ key ]
        
    def __contains__( self, key ):
        return key in self._peer_classes

    def items( self ):
        return self._peer_classes.items()
