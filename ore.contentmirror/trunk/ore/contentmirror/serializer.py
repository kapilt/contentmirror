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

import sqlalchemy as rdb
from zope import interface, component
from zope.app.container.interfaces import IContainer

from ore.contentmirror import schema, interfaces
from ore.contentmirror.session import Session


class Serializer(object):

    interface.implements(interfaces.ISerializer)

    def __init__(self, context):
        self.context = context

    def add(self):
        registry = component.getUtility(interfaces.IPeerRegistry)
        peer = registry[self.context.__class__]()
        session = Session()
        session.add(peer)
        self._copy(peer)
        return peer

    def update(self):
        peer = schema.fromUID(self.context.UID())
        if peer is None:
            return self.add()
        self._copy(peer)
        return peer

    def delete(self):
        peer = schema.fromUID(self.context.UID())
        if peer is None:
            return
        session = Session()
        session.delete(peer)
        session.flush()

    def move(self):
        if not IContainer.providedBy(self.context):
            return self.update()
        # update contained children paths when the container moves
        peer = schema.fromUID(self.context.UID())
        contained = Session().query(schema.Content).filter(
            rdb.and_(schema.Content.path.startswith(peer.path),
                     schema.Content.id != peer.id))

        # get old and new paths to update contained
        old_containment_path = peer.path
        old_relative_path = peer.relative_path
        interfaces.ISerializer(self.context).update()
        new_containment_path = peer.path
        new_relative_path = peer.relative_path

        # for large trees this might be more efficient sans the
        # peer.
        for content in contained:
            content.path = content.path.replace(
                old_containment_path, new_containment_path)
            content.relative_path = content.relative_path.replace(
                old_relative_path, new_relative_path)
        Session().flush()

    def _copy(self, peer):
        self._copyPortalAttributes(peer)
        peer.transformer.copy(self.context, peer)
        self._copyContainment(peer)

    def _copyPortalAttributes(self, peer):
        peer.portal_type = self.context.portal_type
        peer.content_uid = self.context.UID()
        peer.id = self.context.id

        peer.path = '/'.join(self.context.getPhysicalPath())
        portal_url = getattr(self.context, 'portal_url', None)
        if portal_url:
            peer.relative_path = "/".join(
                portal_url.getRelativeContentPath(self.context))
        wf_tool = getattr(self.context, 'portal_workflow', None)
        if wf_tool is None:
            return
        peer.status = wf_tool.getCatalogVariablesFor(
            self.context).get('review_state')

    def _copyContainment(self, peer):
        container = self.context.getParentNode()
        if container is None:
            return
        uid = getattr(container, 'UID', None)
        if uid is None:
            return
        uid = uid()
        container_peer = schema.fromUID(uid)
        if not container_peer:
            serializer = interfaces.ISerializer(container, None)
            if not serializer:
                return
            container_peer = serializer.add()
        peer.parent = container_peer
