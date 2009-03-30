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

import threading, transaction
from zope import interface, component
from ore.contentmirror.session import Session
from ore.contentmirror import interfaces

class Operation( object ):
    
    interface.implements( interfaces.IOperation )

    filtered = False
    
    def __init__( self, context ):
        self.context = context
        
    @property
    def document_id( self ):
        return self.context.UID()
        
    def process( self ):
        raise NotImplementedError("subclass responsibility")

class AddOperation( Operation ):

    interface.implements( interfaces.IAddOperation )

    def process( self ):
        interfaces.ISerializer( self.context).add()
        
class UpdateOperation( Operation ):

    interface.implements( interfaces.IUpdateOperation )

    def process( self ):
        interfaces.ISerializer( self.context).update()
        
class DeleteOperation( Operation ):
    
    interface.implements( interfaces.IDeleteOperation )
    
    def process( self ):
        interfaces.ISerializer( self.context ).delete()
        
class OperationFactory( object ):

    interface.implements( interfaces.IOperationFactory )

    __slots__ = ('context',)

    def __init__( self, context ):
        self.context = context
    
    def add( self ):
        return self._store( AddOperation( self.context ) )

    def update( self ):
        return self._store( UpdateOperation( self.context ) )

    def delete( self ):
        return self._store( DeleteOperation( self.context ) )
        
    def _store( self, op ):
        # apply filters to operation
        component.subscribers( (self.context, op ), interfaces.IFilter )
        if op.filtered:
            return
        get_buffer().add( op )
        
class BufferManager( object ):

    def __init__( self, context ):
        self.context = context

    def abort( self, *args ):
        self.context.clear()

    def nothing( self, *args ): pass

    def sortKey( self ):
        return "content-mirror-2008"
    
    tpc_abort = abort
    commit = tpc_begin = tpc_vote = tpc_finish = nothing
    
class OperationBuffer( object ):
    """
    an operation buffer aggregates operations across a transaction
    """

    def __init__( self ):
        self.ops = {}
        self.registered = False

    def add( self, op ):
        """add an operation to the buffer, aggregating with existing operations"""
        doc_id = op.document_id
        previous = self.ops.get( doc_id )
        if previous is not None:
            op = self._choose( previous, op)
        if op is None: # none returned when ops cancel
            del self.ops[ doc_id ]
            return
        self.ops[ doc_id ] = op
        if not self.registered:
            self._register()

    def clear( self ):
        self.ops = {}
        self.registered = False
        self.manager = None

    def flush( self ):
        for op in self:
            op.process()
        Session().flush()
        self.clear()
        
    def get( self, doc_id ):
        return self.ops.get( doc_id )
        
    def __iter__( self ):
        for op in self.ops.values():
            yield op
            
    def _register( self ):
        self.registered = True
        transaction.get().addBeforeCommitHook( self.flush )
        transaction.get().join( BufferManager( self ) )

    def _choose( self, previous, new ):
        """
        for a given content object, choose one operation to perform given
        two candidates. can also return no operations.
        """
        p_kind = (interfaces.IDeleteOperation.providedBy( previous ) and 2) \
                 or (interfaces.IAddOperation.providedBy( previous ) and 1) \
                 or (interfaces.IUpdateOperation.providedBy( previous ) and 0)
                 
        n_kind = (interfaces.IDeleteOperation.providedBy( new ) and 2) \
                 or (interfaces.IAddOperation.providedBy( new ) and 1) \
                 or (interfaces.IUpdateOperation.providedBy( new ) and 0)

        # if we have an add and then a delete, its an effective no-op
        if ( p_kind == 1 and n_kind == 2 ):
            return None
        if p_kind > n_kind:
            return previous
        return new

_buffer = threading.local()

def get_buffer( ):
    op_buffer = getattr( _buffer, 'buffer', None)
    if op_buffer is not None:
        return op_buffer
    op_buffer = OperationBuffer()
    _buffer.buffer = op_buffer
    return op_buffer
