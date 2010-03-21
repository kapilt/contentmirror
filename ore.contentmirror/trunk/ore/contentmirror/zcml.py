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

from zope import component
#from zope.app.component.metaconfigure import utility
#from zope.component.security import PublicPermission

import sqlalchemy
from ore.contentmirror import interfaces
from ore.contentmirror import loader

from zope.configuration import fields
#from zope import interface

from zope.component import zcml


class IContentMirror(interface.Interface):

    content = fields.GlobalObject(
        title=u"Content Class to be Mirrored")

    serializer = fields.GlobalObject(
        title=u"Serializer For the Content",
        required=False)

    transformer = fields.GlobalObject(
        title=u"Schema Transformer",
        required=False)


def mirror(_context, content, serializer=None, transformer=None):

    if not interfaces.IMirrored.implementedBy(content):
        interface.classImplements(content, interfaces.IMirrored)

    if serializer:
        zcml.adapter(_context,
                     (serializer,),
                     interfaces.ISerializer,
                     (content,))

    if transformer:
        zcml.adapter(_context,
                     (transformer,),
                     interfaces.ISchemaTransformer,
                     (content, interfaces.IMetaData))

    _context.action(
        discriminator = (content, interfaces.IMirrored),
        callable = loader.load,
        args = (content,))


class IEngineDirective(interface.Interface):
    """ Creates A Database Engine. Database Engines are named utilities.
    """
    url = schema.URI(title = u'Database URL',
                     description = u'SQLAlchemy Database URL',
                     required = True)

    name = schema.Text(title = u'Engine Name',
                       description=u"Empty if this is the default engine",
                       required = False,
                       default = u'')

    echo = schema.Bool(title = u'Echo SQL statements',
                       description = u'Debugging Log for Database Engine',
                       required = False,
                       default=False)

    pool_recycle = schema.Int(title = u"Connection Recycle",
                              description=u"Time Given in Seconds",
                              required = False,
                              default = -1)


# keyword arguments to pass to the engine
IEngineDirective.setTaggedValue('keyword_arguments', True)


def engine(_context, url, name='', echo=False, pool_recycle=-1, **kwargs):

    engine_component = sqlalchemy.create_engine(
        url, echo=echo,
        pool_recycle=pool_recycle, **kwargs)

    zcml.utility(_context,
                 provides = interfaces.IDatabaseEngine,
                 component = engine_component,
                 name = name)


class IBindDirective(interface.Interface):
    """ Binds a MetaData to a database engine."""

    engine = schema.Text(title = u"Engine Name")

    metadata = fields.GlobalObject(
        title=u"Metadata Instance",
        description = u"Metadata Instance to be bound")


def bind(_context, engine, metadata):

    def _bind(engine_name, metadata):
        metadata.bind = component.getUtility(
            interfaces.IDatabaseEngine, engine)

    _context.action(
        discriminator = ('alchemist.bind', metadata),
        callable = _bind,
        args = (engine, metadata))
