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
#metadata.bind = rdb.create_engine('postgres://localhost/rescueme')

ContentSequence = rdb.Sequence('content_sequence')

content = rdb.Table(
   "content",
   metadata,
   rdb.Column( "content_id", rdb.Integer, ContentSequence, primary_key=True ),
   rdb.Column( "uid", rdb.String(36), nullable=False ),
   rdb.Column( "portal_type", rdb.String(64) ),
   rdb.Column( "status", rdb.Unicode(64) ),   
   rdb.Column( "type", rdb.String(64) ),
   rdb.Column( "container_id", rdb.Integer, rdb.ForeignKey('content.content_id') ),
   # dublin core
   rdb.Column( "title", rdb.UnicodeText ),
   rdb.Column( "description", rdb.UnicodeText ),
   rdb.Column( "subject", rdb.UnicodeText ),
   rdb.Column( "location", rdb.UnicodeText(4000) ),
   rdb.Column( "contributors", rdb.UnicodeText ),
   rdb.Column( "creators", rdb.UnicodeText ),
   rdb.Column( "creation_date", rdb.DateTime ),
   rdb.Column( "modification_date", rdb.DateTime ),
   rdb.Column( "effective_date", rdb.DateTime  ),
   rdb.Column( "expiration_date", rdb.DateTime ),
   rdb.Column( "language", rdb.Unicode(32)  ),
   rdb.Column( "rights", rdb.UnicodeText ),
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
#orm.mapper( Node, content,

            
#def fromId( content_id ):
#    return Session().query( Content ).get( content_id )
    
def fromUID( content_uid ):
    return Session().query( Content ).autoflush(False).filter( Content.c.uid == content_uid ).first()
                
relations = rdb.Table(
   "relations",
   metadata,
   rdb.Column( "source_id", rdb.Integer, rdb.ForeignKey('content.content_id', ondelete='CASCADE'),
               primary_key=True ),
   rdb.Column( "target_id", rdb.Integer, rdb.ForeignKey('content.content_id', ondelete='CASCADE'),
               primary_key=True),
   rdb.Column( "relationship", rdb.Unicode(128), primary_key=True )
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

   

    


