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

from sqlalchemy import orm
from zope import interface

from ore.contentmirror import schema, interfaces


class PeerFactory(object):

    interface.implements(interfaces.IPeerFactory)

    def __init__(self, context, transformer):
        self.context = context
        self.transformer = transformer

    @property
    def name(self):
        return self.context.__class__.__name__ + 'Peer'

    def make(self):
        klass = type(self.name, (schema.Content,),
                     dict(transformer=self.transformer))

        # With single value references creating additional foreign
        # keys to the content table, we need to distinguish the
        # join condition for the class inheritance.
        if self.transformer.table:
            # unit tests exercise a custom transformer without a table.
            join_clause = (
                self.transformer.table.c.content_id == \
                schema.content.c.content_id)
        else:
            join_clause = None

        orm.mapper(klass,
                   self.transformer.table,
                   properties=dict(self.transformer.properties),
                   inherits=schema.Content,
                   inherit_condition=join_clause,
                   polymorphic_on=schema.content.c.object_type,
                   polymorphic_identity=self.name)
        return klass


class PeerRegistry(object):

    interface.implements(interfaces.IPeerRegistry)

    def __init__(self):
        self._peer_classes = {}

    def __setitem__(self, key, value):
        self._peer_classes[key] = value

    def __getitem__(self, key):
        """
        Lookup the peer class using the content class as the key. If
        not found try find a peer using the content's base classes.
        Either returns a suitable peer class or raises a KeyError.
        """
        if key in self._peer_classes:
            return self._peer_classes[key]

        for base in key.mro():
            factory = self._peer_classes.get(base, None)
            if factory is not None:
                self._peer_classes[key] = factory # cache
                break
        return self._peer_classes[key]

    def __contains__(self, key):
        # must not check base classes here
        return key in self._peer_classes

    def items(self):
        return self._peer_classes.items()
