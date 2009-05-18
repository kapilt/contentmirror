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

import time
import interfaces
import logging
from zope import interface, component

from ore.contentmirror import session

log = logging.getLogger('mirror.async')

class AsyncProcessor( object ):

    interface.implements( interfaces.IProcessor )
    
    def __init__( self, db, site_path, transport, daemon=False ):
        self.db = db
        self.transport = transport
        self.site_path = site_path
        self.daemon = False

    def __call__( self ):
        while 1:
            try:
                self._process()
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception, e:
                log.exception("Error %s"%e)
                if not self.daemon:
                    raise                    
            if not self.daemon:
                break
        
            time.sleep( interfaces.POLL_INTERVAL )
            
    def _traverse( self, root ):
        site = root.unrestrictedTraverse( self.site_path )
        loader = component.getUtility( interfaces.IOperationLoader )
        loader.setSite( site )
        return site
        
    def _process( self ):
        log.info('Opening ZODB Connection')
        # open a zodb connection
        connection = self.db.open()
        
        # retrieve the plone site root, and set up the operation loader with it
        self._traverse( connection.root() )
        
        # fetch operations from the transport
        log.info("Polling For Operations")
        for op in self.transport.poll():
            log.info("Processing Operation %s"%(op))
            
            # process the content mirror operation
            op.process()
            
            # notify the transport that we're done with this operation
            # ( so it can do permanent removal from queue )
            self.transport.processed( op )
            
            # resync state of zodb connection, not sure if this really
            # needed, but prefer correctness over speed
            connection.sync()
            
        log.info("Flushing session")
        session.Session().flush()
        connection.close()

