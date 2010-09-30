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
The Model Loader drives the startup bootstrapping, its wired into the
zcml directives, its responsible for loading/generating the tables,
and creating the rdb mapped peer classes.

"""
from zope import component
from ore.contentmirror import schema, interfaces, plone


class ModelLoader(object):

    def __init__(self, metadata):
        self.metadata = metadata

    def load(self, klass):
        plone.push(klass) # simulate required plone environment for content
        try:
            instance = klass("transient")
        finally:
            plone.pop(klass) # remove simulated environment

        registry = component.queryUtility(interfaces.IPeerRegistry)
        if klass in registry:
            raise KeyError("Duplicate %r"%klass)

        transformer = self.transform(instance)
        peer_class = self.peer(instance, transformer)

        registry[klass] = peer_class

    def transform(self, instance):
        transformer = component.getMultiAdapter((instance, self.metadata),
                                                interfaces.ISchemaTransformer)
        transformer.transform()
        return transformer

    def peer(self, instance, transformer):
        factory = component.getMultiAdapter((instance, transformer),
                                             interfaces.IPeerFactory)
        return factory.make()

loader = ModelLoader(schema.metadata)
load = loader.load
