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

from zope import interface

import schema, interfaces

class PeerFactory( object ):
    
    interface.implements( interfaces.IPeerFactory )
    
    def __init__( self, context, transformer ):
        self.context = context
        self.transformer = transformer
        
    def make( self ):
        klass = schema.Content[self.context.portal_type]
        klass.transformer = self.transformer
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
