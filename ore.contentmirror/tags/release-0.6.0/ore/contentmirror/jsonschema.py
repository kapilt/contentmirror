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
"""
Export the Archetypes Schema Information for Mirrored Type as JSON

Advanced use cases for content mirror want to have a fuller
introspection of the origin archetypes schema.

A couple of concrete examples that we want to fulfill

 - Extracting Static Vocabularies ( as defined in
   Archetypes.Field.Field.Vocabulary ) for use by the front end.

 - Capturing database encoding of certain multi value fields. Ie. a
   linesfield, will serialize a list of strings to a string with
   newline separated values. A mirror front end may want to introspect
   this sort of information

 - Capturing schemata for customizing mirror front end display.
"""

import simplejson
import os
import sys

from ore.contentmirror import interfaces
from zope import component


def extract_vocabulary(vocabulary):

    # string denotes dynamic vocabulary based on instance method, skip
    if isinstance(vocabulary, str):
        return

    # process simple values directly specified as vocabulary
    if isinstance(vocabulary, (list, tuple)):
        if isinstance(vocabulary[0], (list, tuple)):
            return [(v[0], v[1]) for v in vocabulary]
        if isinstance(vocabulary[0], basestring):
            return [(v, v) for v in vocabulary]

    # process something displaylist like
    if interfaces.IDisplayList.providedBy(vocabulary):
        return vocabulary.items()


def serialize_schema(info):
    klass, peer_klass = info
    instance = klass('transient')
    schema = instance.Schema()

    fields = []
    for f in schema.fields():
        ftransform = component.getMultiAdapter((f, peer_klass.transformer))
        fd = dict(
            name = f.__name__,
            column_name = getattr(ftransform, 'name', ''),
            type = f.__class__.__name__,
            schemata = f.schemata,
            )
        if f.vocabulary:
            vocabulary = extract_vocabulary(f.vocabulary)
            if vocabulary:
                fd['vocabulary'] = vocabulary
        fields.append(fd)

    cd = dict(
        name = klass.__name__,
        table_name = peer_klass.transformer.name,
        fields = fields)
    return cd


def main():
    if len(sys.argv) == 2:
        fh = open(os.path.expanduser(
            os.path.expandvars(sys.argv[1].strip())), 'w')
    else:
        fh = sys.stdout

    registry = component.getUtility(interfaces.IPeerRegistry)
    values = map(serialize_schema, registry.items())
    fh.write(simplejson.dumps({'types': values}))
    fh.close()
