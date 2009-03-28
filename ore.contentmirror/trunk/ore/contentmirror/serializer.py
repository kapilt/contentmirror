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
from ore.contentmirror import schema, interfaces
from ore.contentmirror.session import Session

class Serializer( object ):

    interface.implements( interfaces.ISerializer )
    
    def __init__( self, context ):
        self.context = context
                
    def add( self ):
        registry = component.getUtility( interfaces.IPeerRegistry )
        peer = registry[ self.context.__class__ ]()
        session = Session()
        session.add( peer )        
        self._copy( peer )
        return peer
        
    def update( self ):
        peer = schema.fromUID( self.context.UID() )
        if peer is None:
            return self.add()
        self._copy( peer )
        return peer
        
    def delete( self ):
        peer = schema.fromUID( self.context.UID() )
        if peer is None:
            return
        session = Session()
        session.delete( peer )
        session.flush()

    def _copy( self, peer ):
        self._copyPortalAttributes( peer )
        peer.transformer.copy( self.context, peer )        
        self._copyContainment( peer )
        
    def _copyPortalAttributes( self, peer ):
        peer.portal_type = self.context.portal_type
        peer.uid = self.context.UID()
        peer.id  = self.context.id

        peer.path = '/'.join( self.context.getPhysicalPath() )

        wf_tool = getattr( self.context, 'portal_workflow', None )
        if wf_tool is None: return
        peer.status = wf_tool.getCatalogVariablesFor( self.context ).get('review_state')
        
    def _copyContainment( self, peer ):
        container = self.context.getParentNode()
        if container is None:
            return
        uid = getattr( container, 'UID', None)
        if uid is None: return
        uid = uid()
        container_peer = schema.fromUID( uid )
        if not container_peer:
            serializer = interfaces.ISerializer( container, None )
            if not serializer: return
            container_peer = serializer.add()
        peer.parent = container_peer

        
    
        
