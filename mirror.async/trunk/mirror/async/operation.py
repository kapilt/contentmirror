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
######################################################################

from ore.contentmirror import operation 
from ore.contentmirror.interfaces import IOperationBufferFactory

from zope import interface, component
import interfaces

class AsyncOperationBuffer( operation.OperationBuffer ):
    
    interface.implements( interfaces.IAsyncOperationBuffer )
    
    def flush( self ):
        transport = component.getUtility( interfaces.ITransport )
        map( transport.publish, self)
        self.clear()

class AsyncOperationBufferFactory( object ):
    
    interface.implements( IOperationBufferFactory )
    
    def new( self ):
        return AsyncOperationBuffer()
        
class OperationIO( object ):
    
    # todo - allow more arbitrary things
    
    interface.implements( interfaces.IOperationSerializer, 
                          interfaces.IOperationLoader )
    
    op_map = {'AddOperation':operation.AddOperation,
              'DeleteOperation':operation.DeleteOperation,
              'UpdateOperation':operation.UpdateOperation }

    def __init__( self, op=None):
        self.op = op

    def serialize( self ):
        oid = self.op.document_id        
        name = self.op.__class__.__name__
        return "%s:%s"%( name, oid)
        
    def load( self, state, m ):
        klass_spec, uid = state.split(':')
        klass = self.op_map[ klass_spec ]
        try:
            content = self.site.reference_catalog.lookupObject( uid )
        except KeyError:
            content = None
        op = klass( content )
        op.msg = m
        return op
        
    def setSite( self, site ):
        self.site = site
        
        
        
        
        
