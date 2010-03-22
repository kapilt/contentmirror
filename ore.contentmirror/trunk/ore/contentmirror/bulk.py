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
import transaction
import time
import sys
from ore.contentmirror import interfaces

# installs the zope transaction sqlalchemy integration
from ore.contentmirror.session import Session


def expunge(ob):
    try:
        ob._p_deactivate()
    except:
        pass


def main(app, instance_path, threshold=500):

    portal = app.unrestrictedTraverse(instance_path)

    from AccessControl.SecurityManagement import newSecurityManager
    admin=app.acl_users.getUserById("admin")
    newSecurityManager(None, admin)

    count = 0

    start_time = time.time()
    batch_time = start_time

    portal_catalog = portal.portal_catalog
    for brain in portal_catalog.unrestrictedSearchResults(sort_on='created'):

        try:
            ob = brain.getObject()
            # skip broken objects
            if not ob.UID():
                continue
        except:
            continue

        serializer = interfaces.ISerializer(ob, None)
        if serializer is None:
            expunge(ob)
            continue

        count += 1

        # the object may have been processed by as a dependency
        # so we use update, which dispatches to add if no db
        # state is found.
        serializer.update()
        expunge(ob)

        if count % threshold == 0:
            transaction.commit()
            output = ("Processed ", str(count), "in",
                      "%0.2f s"%(time.time()-batch_time))
            sys.stdout.write(" ".join(output)+"\n")
            ob._p_jar._cache.incrgc()
            batch_time = time.time()

    # commit the last batch
    transaction.commit()
    output = ("Processed ", str(count), "in",
              "%0.2f s"%(time.time()-batch_time))
    sys.stdout.write(" ".join(output)+"\n")

    output = ("Finished in", str(time.time()-start_time))
    sys.stdout.write(" ".join(output)+"\n")

if __name__ == '__main__':
    if not len(sys.argv) == 2:
        print "mirror-batch portal_path"
        sys.exit(1)
    main(app = app, instance_path=sys.argv[1].strip())
