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


from zope import interface, schema
from zope.configuration import fields

from zope.app.component.metaconfigure import utility, PublicPermission

try:
    from zope.component import zcml
except ImportError:
    from zope.app.component import metaconfigure as zcml

import interfaces
import loader

from google.appengine.ext.remote_api import remote_api_stub
from google.appengine.ext import db

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
    
class IAppEngineDirective(interface.Interface):
    """named utility for storing GAE configuration"""
    app_id = schema.Text(title=u'Application id',
                         description=u'App Engine application id',
                         required=True,
                        )
    host = schema.Text(title=u'Host',
                       description=u'App Engine hostname',
                       required=True,
                      )
    username = schema.Text(title=u'Username',
                         description=u'App Engine admin user name',
                         required=True,
                        )
    password = schema.Text(title=u'Password',
                         description=u'App Engine admin user password',
                         required=True,
                        )

class DataStore(object):
    def __init__(self,db):
        self.db=db

def appengine(_context,app_id,host,username,password):
    auth_func = lambda:(username,password)
    remote_api_stub.ConfigureRemoteDatastore(app_id,'/content_mirror',auth_func,host)
    datastore = DataStore(db)
    utility(_context,
            provides=interfaces.IAppEngine,
            component=datastore,
            permission=PublicPermission,
            name='appengine'
           )
