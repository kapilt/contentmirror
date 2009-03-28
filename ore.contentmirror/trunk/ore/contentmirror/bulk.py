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
"""
./bin/zopectl run mirror-batch PORTAL_PATH

a content mirror bulk importer

"""
import transaction, time, sys
from ore.contentmirror import interfaces
from ore.contentmirror.session import Session

def expunge( ob ):
    try: ob._p_deactivate()
    except:pass
        
def main( app ):
    if not len(sys.argv) == 2:
        print "mirror-batch portal_path"
        sys.exit(1)
        
    instance_path = sys.argv[1]
    portal = app.unrestrictedTraverse( instance_path )
     
    threshold = 500
    count = 0
    
    start_time = time.time()
    batch_time = start_time
    
    for brain in portal.portal_catalog(sort_on='created'):

        try: 
            ob = brain.getObject()
            # skip broken objects
            if not ob.UID(): 
                continue
        except: continue
        
        serializer = interfaces.ISerializer( ob, None )
        if serializer is None:
            expunge( ob )
            continue
        
        count += 1

        # the object may have been processed by as a dependency
        # so we use update, which dispatches to add if no db
        # state is found.
        serializer.update()
        expunge( ob )
        
        if count % threshold == 0:

            transaction.commit()
            print "Processed ", count, "in", "%0.2f s"%(time.time()-batch_time)            
            ob._p_jar._cache.incrgc()
            batch_time = time.time()

    # commit the last batch
    transaction.commit()
    print "Processed ", count, "in", "%0.2f s"%(time.time()-batch_time)
    print "Finished in", time.time()-start_time
        
if __name__ == '__main__':
    
    try:
        main( app = app )        
    except:
        import sys,traceback, pdb
        traceback.print_exc()
        pdb.post_mortem(sys.exc_info()[-1])
        raise
