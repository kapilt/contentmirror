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

from zope import interface, component

import interfaces

from boto import sqs
                                                                                                                                                                      
class SQSTransport( object ):    
    
    # boto will put keys from environment variables if present as
    # AWS_ACCESS_KEY_ID - Your AWS Access Key ID
    # AWS_SECRET_ACCESS_KEY - Your AWS Secret Access Key                                                                                                                                           
                 
    interface.implements( interfaces.ITransport )                                                                                                                                                     
    
    def __init__( self, 
                  access_key_id=None,
                  secret_key=None,
                  queue = interfaces.QUEUE_ID,
                  connection = None
                  ):                                                                                                                                      
        self.access_key_id = access_key_id
        self.secret_key = secret_key
        self.queue_id = queue
        self.connection = connection
        
        if not self.connection:
            self.connection = sqs.SQSConnection( self.access_key_id, self.secret_key )
        self.queue = self.connection.create_queue( self.queue_id )
                                                                                                                                                                      
    def publish( self, op ):          
        body = interfaces.IOperationSerializer( op ).serialize()
        msg = sqs.Message( body=body )                                                                                                                                    
        self.queue.write( msg )
        
    def processed( self, operation ):
        msg = getattr( operation, 'msg', None)
        if not msg: return True
        self.queue.delete( msg )
        
    def poll( self ):
        loader = component.getUtility( interfaces.IOperationLoader )
        for i in self.queue.get_messages( 10 ):
            yield loader.load( i.get_body(), i )




                                          
