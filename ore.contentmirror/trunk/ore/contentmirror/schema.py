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

cms content model

"""
import os
from zope import interface
from sqlalchemy import orm, create_engine
import sqlalchemy as rdb

from ore.contentmirror.session import Session
from ore.contentmirror import interfaces

metadata = rdb.MetaData()


def environ_db():
    if os.environ.get('CONTENTMIRROR_URI'):
        metadata.bind=create_engine(os.environ['CONTENTMIRROR_URI'])

environ_db() # set database from the environment

ContentSequence = rdb.Sequence('content_sequence')

content = rdb.Table(
   "content",
   metadata,
   rdb.Column("content_id", rdb.Integer, ContentSequence, primary_key=True),
   rdb.Column("id", rdb.String(256), nullable=False),
   rdb.Column("content_uid", rdb.String(36), nullable=False),
   rdb.Column("object_type", rdb.String(64)),
   rdb.Column("status", rdb.String(64)),
   rdb.Column("portal_type", rdb.String(64)),
   rdb.Column("folder_position", rdb.Integer),
   rdb.Column("container_id", rdb.Integer,
              rdb.ForeignKey('content.content_id', ondelete="CASCADE")),
   rdb.Column("path", rdb.Text),
   rdb.Column("relative_path", rdb.Text),
   # dublin core
   rdb.Column("title", rdb.Text),
   rdb.Column("description", rdb.Text),
   rdb.Column("subject", rdb.Text),
   rdb.Column("location", rdb.Text(4000)),
   rdb.Column("contributors", rdb.Text),
   rdb.Column("creators", rdb.Text),
   rdb.Column("creation_date", rdb.DateTime),
   rdb.Column("modification_date", rdb.DateTime),
   rdb.Column("effectivedate", rdb.DateTime),
   rdb.Column("expirationdate", rdb.DateTime),
   rdb.Column("language", rdb.Text(32)),
   rdb.Column("rights", rdb.Text),
   # plone
   rdb.Column("excludefromnav", rdb.Boolean))


rdb.Index('content_content_uid_idx', content.c.content_uid, unique=True)
rdb.Index('content_modification_date_idx', content.c.modification_date)

relations = rdb.Table(
   "relations",
   metadata,
   rdb.Column("source_id", rdb.Integer,
               rdb.ForeignKey('content.content_id', ondelete='CASCADE'),
               primary_key=True),
   rdb.Column("target_id", rdb.Integer,
               rdb.ForeignKey('content.content_id', ondelete='CASCADE'),
               primary_key=True),
   rdb.Column("relationship", rdb.String(128), primary_key=True))

files = rdb.Table(
    "files",
    metadata,
    rdb.Column("content_id", rdb.Integer,
               rdb.ForeignKey('content.content_id', ondelete="CASCADE"),
               primary_key=True),
    rdb.Column("attribute", rdb.String(156), primary_key=True),
    rdb.Column("type", rdb.String(30)),
    rdb.Column("content", rdb.Binary),
    rdb.Column("path", rdb.String(300)),
    rdb.Column("file_size", rdb.Integer),
    rdb.Column("checksum", rdb.String(33)),
    rdb.Column("file_name", rdb.String(156)),
    rdb.Column("mime_type", rdb.String(80)),
   )

rdb.Index('files_idx',
      files.c.content_id,
      files.c.attribute,
      unique=True)


class Content(object):
    type = "content"
    interface.implements(interfaces.IContentPeer)


class Relation(object):

    def __init__(self, source=None, target=None, relation=None):
        self.source = source
        self.target = target
        self.relationship = relation

orm.mapper(Content, content,
            polymorphic_on=content.c.object_type,
            polymorphic_identity='content',
            properties = {
               'children': orm.relation(
                   Content,
                   backref=orm.backref('parent',
                                       remote_side=[content.c.content_id])),
               'relations': orm.relation(
                   Relation,
                   cascade="all, delete-orphan",
                   primaryjoin=(content.c.content_id==relations.c.source_id),
                   backref=orm.backref("source",
                                       remote_side=[relations.c.source_id]))})
#               'backrefs': orm.relation(
#                   Relation,
#                   primaryjoin=(content.c.content_id==relations.c.target_id),
#                   backref=orm.backref("target",
#                                       remote_side=[relations.c.target_id]))})


#class Node( object ): pass
#orm.mapper( Node, content )

class UIDFilter(object):

    __slots__ = ('uid',)

    def __init__(self, uid):
        self.uid = uid

    def __call__(self, ob):
        if not interfaces.IContentPeer.providedBy(ob):
            return False
        return ob.content_uid == self.uid


def fromUID(content_uid):
    """
    fetch an object by uid, does not flush the session, and also checks
    against new objects in the sqlalchemy session.
    """
    session = Session()
    peers = filter(UIDFilter(content_uid), session.new)
    if peers:
        return peers.pop()
    return session.query(Content).autoflush(False).filter(
        content.c.content_uid == content_uid).first()


orm.mapper(Relation, relations,
           properties = {
#               'source': orm.relation(
#                   Content, uselist=False, backref='relations',
#                   primaryjoin=content.c.content_id==relations.c.source_id),
               'target': orm.relation(
                   Content, uselist=False,
                   primaryjoin=content.c.content_id==relations.c.target_id)})


class File(object):
    """A Database contained file. """

orm.mapper(File, files,
           polymorphic_on=files.c.type,
           polymorphic_identity='db-file')
