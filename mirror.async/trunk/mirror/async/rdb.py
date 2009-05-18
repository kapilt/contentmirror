

from zope import interface, component
from ore.contentmirror.schema import metadata
import sqlalchemy as rdb
import interfaces

message_queue = rdb.Table(
    "message_queue",
    metadata,
    rdb.Column("message_id", rdb.Integer, primary_key=True ),
    rdb.Column("state", rdb.String(256) )
    )

class RDBTransport( object ):

    interface.implements( interfaces.ITransport )
    
    def publish( self, op ):
        body = interfaces.IOperationSerializer( op ).serialize() 
        message_queue.insert().values( state=body ).execute()        

    def processed( self, op ):
        msg = getattr( op, 'msg', None)
        if not msg: return True
        message_queue.delete( message_queue.c.message_id == msg ).execute()

    def poll( self ):
        loader = component.getUtility( interfaces.IOperationLoader )        
        for i in message_queue.select().execute():
            yield loader.load( i.state, i.message_id )
            
    

        
    
