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
import optparse

import sqlalchemy as rdb
from ore.contentmirror import interfaces, session, schema
from DateTime import DateTime

# pyflakes
session


def expunge(ob):
    try:
        ob._p_deactivate()
    except:
        pass


def setup_parser():
    parser = optparse.OptionParser(
        usage="usage: ./bin/instance run ./bin/%prog [options] portal_path")
    parser.add_option(
        '-i', '--incremental', dest="incremental", action="store_true",
        help="serialize content modified/created since last run",
        default=False)
    parser.add_option(
        '-t', '--types', dest="types", default="",
        help="only serialize specified types (comma separated)")
    parser.add_option(
        '-p', '--path', dest="path", default="",
        help="serialize content from the specified path")
    parser.add_option(
        '-q', '--quiet', dest='verbose', action='store_false',
        help="quiet/silent output", default=True)
    parser.add_option(
        '-b', '--batch', dest='threshold', type="int",
        help="batch commit every N objects (default %s)"%(500), default=500)
    parser.add_option(
        '-d', '--db', dest='database', default="",
        help="use the specified database uri")
    return parser


def setup_query(options):
    """
    Setup a portal catalog query based on query parameters.

    Any filtering of content will still automatically pull in containers and
    referenced items of matched content regardless of whether they match
    the query to maintain consistency.
    """
    # sorting on created, gets us containers before children
    query = {'sort_on': 'created'}

    # sync by type
    if options.types:
        types = filter(None, [t.strip() for t in options.types.split(',')])
        if types:
            query['portal_type'] = {'query': types, 'operator': 'or'}

    # sync by folder
    if options.path:
        path = filter(None, [p.strip() for p in options.path.split(',')])
        if path:
            query['path'] = {'query': path, 'depth': 0, 'operator': 'or'}

    # incremental sync, based on most recent database content date.
    if options.incremental:
        last_sync_query = rdb.select(
            [rdb.func.max((schema.content.c.modification_date))])
        last_sync = last_sync_query.execute().scalar()
        if last_sync: # increment 1s
            time_tuple = list(last_sync.timetuple())
            time_tuple[4] = time_tuple[4]+1
            last_sync = DateTime(time.mktime(tuple(time_tuple)))
            query['modified'] = {'query': last_sync, 'range': 'min'}

    return query


def get_app():
    frame = sys._getframe(2)
    return frame.f_locals.get('app')


def main(app=None, instance_path=None, threshold=500):
    parser = setup_parser()
    options, args = parser.parse_args()

    if len(args) != 1:
        parser.print_help()
        sys.exit(1)
        return

    if app is None:
        app = get_app()

    if options.database:
        schema.metadata.bind = rdb.create_engine(options.database)

    instance_path = args[0]
    portal = app.unrestrictedTraverse(instance_path)

    count = 0 # how many objects have we processed

    start_time = time.time()
    batch_time = start_time # we track the time for each batch
    # sorting on created, gets us containers before children
    query = {'sort_on': 'created'}

    query = setup_query(options)
    for brain in portal.portal_catalog.unrestrictedSearchResults(**query):
        try:
            ob = brain.getObject()
            # skip broken objects
            if not ob.UID():
                continue
        except: # got to keep on moving
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
            if options.verbose:
                output = ("Processed ", str(count), "in",
                          "%0.2f s"%(time.time()-batch_time))
                sys.stdout.write(" ".join(output)+"\n")
            ob._p_jar._cache.incrgc()
            batch_time = time.time()

    # commit the last batch
    transaction.commit()

    if options.verbose:
        output = ("Processed ", str(count), "in",
                  "%0.2f s"%(time.time()-batch_time))
        sys.stdout.write(" ".join(output)+"\n")

    if options.verbose:
        output = ("Finished in", str(time.time()-start_time))
        sys.stdout.write(" ".join(output)+"\n")
