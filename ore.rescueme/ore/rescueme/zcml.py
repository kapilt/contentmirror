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


import loader

from zope.configuration import fields
from zope import interface
from zope.component import zcml

import interfaces

class IContentMirror( interface.Interface ):

    content = fields.GlobalObject(
        title=u"Content Class to be Mirrored",
        )

    serializer = fields.GlobalObject(
        title=u"Serializer For the Content",
        required=False
        )

    transformer = fields.GlobalObject(
        title=u"Schema Transformer",
        required=False
        )
    
def mirror( _context, content, serializer=None, transformer=None ):

    if not interfaces.IMirrored.implementedBy( content ):
        interface.classImplements( content, interfaces.IMirrored )

    if serializer:
        zcml.adapter( _context,
                      serializer,
                      interfaces.ISerializer,
                      content,
                      )

    if transformer:
        zcml.adapter( _context,
                      serializer,
                      interfaces.ISchemaTransformer,
                      content,
                      )        

    _context.action(
        discriminator = ( content, interfaces.IMirrored ),
        callable = loader.load,
        args = ( content, )
        )
    
        
                      
        
        
        
