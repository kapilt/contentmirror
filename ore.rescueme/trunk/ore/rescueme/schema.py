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

from sqlalchemy import orm
from zope import interface
import sqlalchemy as rdb

from ore.alchemist import Session
from ore.rescueme import interfaces

metadata =  rdb.MetaData()

ContentSequence = rdb.Sequence('content_sequence')

content = rdb.Table(
   "content",
   metadata,
   rdb.Column( "content_id", rdb.Integer, ContentSequence, primary_key=True ),
   rdb.Column( "id", rdb.String(256), nullable=False ),
   rdb.Column( "uid", rdb.String(36), nullable=False ),
   rdb.Column( "portal_type", rdb.String(64) ),
   rdb.Column( "status", rdb.String(64) ),   
   rdb.Column( "type", rdb.String(64) ),
   rdb.Column( "container_id", rdb.Integer, rdb.ForeignKey('content.content_id') ),
   # dublin core
   rdb.Column( "title", rdb.Text ),
   rdb.Column( "description", rdb.Text ),
   rdb.Column( "subject", rdb.Text ),
   rdb.Column( "location", rdb.Text(4000) ),
   rdb.Column( "contributors", rdb.Text ),
   rdb.Column( "creators", rdb.Text ),
   rdb.Column( "creation_date", rdb.DateTime ),
   rdb.Column( "modification_date", rdb.DateTime ),
   rdb.Column( "effectiveDate", rdb.DateTime  ),
   rdb.Column( "expirationDate", rdb.DateTime ),
   rdb.Column( "language", rdb.Text(32)  ),
   rdb.Column( "rights", rdb.Text ),
   )

rdb.Index('content_uid_idx', content.c.uid, unique=True )
   
class Content( object ):
    type = "content"
    interface.implements( interfaces.IContentPeer )

orm.mapper( Content, content, 
            polymorphic_on=content.c.type,
            polymorphic_identity='content',
            properties = { 'children':orm.relation(Content,
                    backref=orm.backref('parent', remote_side=[content.c.content_id])) }
    )           

#class Node( object ): pass   
#orm.mapper( Node, content )
            
class UIDFilter( object ):

    __slots__ = ('uid',)
    
    def __init__( self, uid ):
        self.uid = uid
        
    def __call__( self, ob ):
        if not interfaces.IContentPeer.providedBy( ob ):
            return False
        return ob.uid == self.uid

def fromUID( content_uid ):
    """
    fetch an object by uid, does not flush the session, and also checks 
    against new objects in the sqlalchemy session.
    """
    session = Session()
    peers = filter( UIDFilter( content_uid ), session.new)
    if peers:
        return peers.pop()
    return session.query( Content ).autoflush(False).filter( content.c.uid == content_uid ).first()
                
relations = rdb.Table(
   "relations",
   metadata,
   rdb.Column( "source_id", rdb.Integer, 
               rdb.ForeignKey('content.content_id', ondelete='CASCADE'),
               primary_key=True ),
   rdb.Column( "target_id", rdb.Integer, 
               rdb.ForeignKey('content.content_id', ondelete='CASCADE'),
               primary_key=True),
   rdb.Column( "relationship", rdb.Text(128), primary_key=True )
   )


class Relation( object ):

    def __init__( self, source=None, target=None, relation=None):
        self.source = source
        self.target = target
        self.relationship = relation
   
orm.mapper( Relation, relations,
            properties = {
                'source': orm.relation(Content, uselist=False, backref='relations',
                                       primaryjoin=content.c.content_id==relations.c.source_id ),
                'target': orm.relation(Content, uselist=False,
                                       primaryjoin=content.c.content_id==relations.c.target_id ),
                }
            )

   

    


