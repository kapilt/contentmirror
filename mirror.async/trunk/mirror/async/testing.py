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

from ore.contentmirror.testing import doctest_ns, tearDown, setUp as _setUp
from zope import component

def setUp( test ):
    _setUp( test )
    from ore.contentmirror import interfaces
    from mirror.async import operation, interfaces as async_interfaces
    
    component.getGlobalSiteManager().unregisterUtility( provided=interfaces.IOperationBufferFactory )
    component.provideUtility( operation.AsyncOperationBufferFactory() )
    component.provideAdapter( operation.OperationIO, ( interfaces.IOperation, ), async_interfaces.IOperationSerializer)
    component.provideUtility( operation.OperationIO(), async_interfaces.IOperationLoader )
    
class FakeAMQP( object ):

    _channel = None
    
    def get_channel( self ):
        return self._channel 

    def channel( self ):
        self._channel = FakeAMQPChannel()
        return self._channel
    
class FakeAMQPChannel( object ):

    def __init__( self ):
        self.messages = []
        
    def null( self, *args, **kw):
        pass

    close = basic_ack = access_request = exchange_declare = queue_declare = queue_bind = null

    def publish( self, msg ):
        self.messages.append( msg )

    def basic_get( self, *args, **kw ):
        if self.messages:
            msg = self.messages.pop(0)
            msg.delivery_tag = 'delivered'
            return msg
    
class FakeSQS( object ):

    _channel = None
    
    def get_channel( self ):
        return self._channel
    
    def create_queue( self, name ):
        return FakeSQSQueue()

class FakeSQSQueue( object ):

    def __init__( self ):
        self.messages = []
        
    def write( self, msg ):
        self.messages.append( msg )
    
    def delete( self, msg ):
        self.messages.remove( msg )
        
    def get_messages( self, msg_count=5 ):
        return self.messages[:msg_count]
        
class FakeZODB( object ):
    
    def __init__( self, ctx ):
        self.ctx = ctx
        
    def open( self ):
        return FakeZODBConnection( self.ctx )

class FakeZODBConnection( object ):

    def __init__( self, ctx ):
        self.ctx = ctx
    
    def root( self ):
        return FakeZODBRoot( self.ctx )
        
    def sync( self ):
        pass
        
    def close( self ):
        pass
                 
class FakeZODBRoot( object ):                

    def __init__( self, ctx ):
        self.ctx = ctx
        
    def unrestrictedTraverse( self, path ):
        return FakePloneSite( self.ctx )

class FakeReferenceCatalog(object):
    
    def __init__( self, ctx ):
        self.ctx = ctx
        
    def lookupObject( self, uid ):
        return self.ctx
        
class FakePloneSite( object ):
    
    def __init__( self, ctx ):
        self.reference_catalog = FakeReferenceCatalog( ctx )

def open_zodb( ctx ):
    return FakeZODB( ctx )
    
def clear_db(  ):
    from ore.contentmirror import schema
    import sqlalchemy as rdb
    import transaction    

    stmt = schema.content.delete()
    stmt.execute()
    transaction.commit()

    # sqlite 3.6.3 doesn't seem to like delete a record, and reinserting it with 
    # same pk, work around recreating the entire db        
    if schema.metadata.bind.url.drivername == 'sqlite':
        schema.metadata.bind = rdb.create_engine('sqlite://')
        schema.metadata.create_all()
        
doctest_ns = dict( doctest_ns )
doctest_ns.update( dict(
    _amqp_connection_ = FakeAMQP(),
    _sqs_connection_ = FakeSQS(),
    open_zodb = open_zodb,
    clear_db = clear_db
    ) )
