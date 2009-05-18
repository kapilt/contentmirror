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

import amqplib.client_0_8 as amqp
from zope import component, interface

import interfaces

class AMQPTransport( object ):
    
    interface.implements( interfaces.ITransport )

    def  __init__( self, host=None, user=None, password=None, ssl=None, 
                   realm=interfaces.REALM, 
                   exchange=interfaces.EXCHANGE_ID,
                   exchange_type=interfaces.EXCHANGE_TYPE,
                   queue = interfaces.QUEUE_ID,
                   connection=None ):
                   
        self.user = user
        self.password = password
        self.host = host
        self.ssl = ssl

        self.realm = realm
        self.queue = queue
        self.exchange = exchange
        self.exchange_type = exchange_type
        self.connection = connection
                
        if not self.connection:
            self.connection = amqp.Connection(
                host=self.host, user=self.user, password=self.password, ssl=self.ssl
                )
            
        self.channel = self.connection.channel()
        self.initialized = False
    
    def setup_publisher( self ):
        if self.initialized: return        
        self.channel.access_request( self.realm, active=True, write=True )
        self.channel.exchange_declare( self.exchange, self.exchange_type )
        self.initialized = True
        
    def setup_subscriber( self ):
        if self.initialized: return
        self.channel.access_request( self.realm, active=True, read=True )
        self.channel.exchange_declare( self.exchange, self.exchange_type )        
        self.channel.queue_declare( self.queue, durable=True )
        self.channel.queue_bind( self.queue, self.exchange )
        self.initialized = True
        
    def publish( self, op ):
        if not self.initialized: self.setup_publisher()
        msg = amqp.Message(  interfaces.IOperationSerializer( op ).serialize() )            
        self.channel.publish( msg )
        
    def poll( self ):
        if not self.initialized: self.setup_subscriber()
        loader = component.getUtility( interfaces.IOperationLoader )
        msg = self.channel.basic_get( self.queue, no_ack=True )
        while msg:
            yield loader.load(  msg.body, msg )
            msg = self.channel.basic_get( self.queue, no_ack=True )            

    def processed( self, operation ):
        msg = getattr( operation, 'msg', None)
        if not msg: return
        self.channel.basic_ack( msg.delivery_tag )
        
    def reset( self ):
        self.channel.close()
        self.initialized = False
        

