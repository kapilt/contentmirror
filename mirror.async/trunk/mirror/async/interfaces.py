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

POLL_INTERVAL = 10 # in seconds
EXCHANGE_ID = "contentmirror"
QUEUE_ID = "contentmirror"
EXCHANGE_TYPE = "fanout"
REALM = "contentmirror"

from zope import interface

class IOperationSerializer( interface.Interface ):

    def serialize( ):
        """
        return an operation serialized as a string
        """

class IOperationLoader( interface.Interface ):
    
    def load( state ):
        """
        return an operation object from deserialized state
        """

class IAsyncOperationBuffer( interface.Interface ):
    """
    an operation buffer that on flushing serializes to operations
    """
    
    def flush( ):
        """
        on flushing the operation buffer will flush to the registered async transport 
        """

class ITransport( interface.Interface ):

    def publish( operation ):
        """
        publish operation to message bus via the transport
        """
        
    def processed( operation ):
        """
        after an operation has been successfully processed, this method must be invoked
        to notify the queue that it has been handled successfully, and can be removed
        from the queue
        """
        
    def poll( ):
        """
        return an iterator over messages from the message bus
        """

class IProcessor( interface.Interface ):
    
    def process( operation ):
        """ process an operation """

