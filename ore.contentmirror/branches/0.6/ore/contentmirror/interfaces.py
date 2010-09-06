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
######################################################################
from zope import interface, schema
from zope.component.interfaces import IObjectEvent


class IDatabaseEngine(interface.Interface):
    """
    Configuration and access to a sqlalchemy pooled database connection.
    """


class IMirrored(interface.Interface):
    """
    Marker interface, signifying that the content should be mirrored
    to a database """


class IMetaData(interface.Interface):
    """
    Marker interface for sqlalchemy metadata, to allow for use
    in adaptation.
    """


# Fields already covered by the base peer content class, common to all content
DUBLIN_CORE= [
    "id",
    "contributors",
    "creators",
    "creation_date",
    "description",
    "effectiveDate",
    "expirationDate",
    "language",
    "location",
    "modification_date",
    "rights",
    "subject",
    "title",
    'path',
    # the following aren't dublin core but are common to atct, we include
    # them here to have them filtered by default from the peer table
    "allowDiscussion",
    "excludeFromNav",
    ]

#########################################
# Custom Events
#########################################

class IContainerOrderChangedEvent(IObjectEvent):
    """
    A container event fired when an object within a container has its position.
    Distinguished from container modified events as its more specific to
    positioning events, rather than generic to containment.
    """


class ContainerOrderChanged(object):
    interface.implements(IContainerOrderChangedEvent)

    def __init__(self, object):
        self.object = object

#########################################
# Runtime Serialization
#########################################

class IOperation(interface.Interface):

    oid = schema.ASCIILine(description=u"The identifier for the content")
    filtered = schema.Bool(
        description=u"denotes the operation should be skipped (filter set)")

    def process(connection):
        """
        process an index operation
        """


class IFilter(interface.Interface):
    """ a subscription adapter that can filter objects serialized"""


class IDeleteOperation(IOperation):
    """Operation for when content is deleted."""


class IUpdateOperation(IOperation):
    """Operation for when content is updated."""


class IAddOperation(IOperation):
    """Operation for when content is added."""


class IMoveOperation(IOperation):
    """Operation for when content is moved."""


class IRepositionOperation(IOperation):
    """Operation for when a container has its content ordering changed."""


class IOperationBuffer(interface.Interface):
    """ transactional operation buffer """

    def add(operation):
        """ add an operation to the buffer """

    def flush():
        """ flush the buffer and process/handle the operations """


class IOperationBufferFactory(interface.Interface):
    """ a factory for creating operation buffer instances, as buffers
        are accessed via utilities """


class IOperationFactory(interface.Interface):
        """ """


class ISerializer(interface.Interface):

    def add():
        """
        add the object to the database
        """

    def delete():
        """
        delete the object from the database
        """

    def update():
        """
        update the object state in the database
        """

    def move():
        """
        move the content's container
        """

    def reposition():
        """
        serialize a container's contained content positions
        """

########################################
## Schema Generation
########################################

class IModelLoader(interface.Interface):

    def load(klass):
        """ load a content class"""

    def transform():
        """ return a schema transformer """

    def peer(transformer):
        """ generate a content peer class for the content class """


class ISchemaTransformer(interface.Interface):
    """ translate an archetypes schema to a relational schema """

    metadata = interface.Attribute("metadata")

    def transform():
        """
        return a sqlalchemy database table representation
        """


class IFieldTransformer(interface.Interface):
    """ transforms an archetypes field into a sqlalchemy field """

    def transform():
        """
        returns the equivalent sqlalchemy field
        """

    def copy(instance, peer):
        """
        copies the field value from the instance to the peer.
        """

########################################
## Content Peers
########################################

class IContentPeer(interface.Interface):
    """
    A relational persisted class that has a mirror of attributes
    of a portal content class.
    """

    transformer = schema.Object(ISchemaTransformer)


class IContentFile(interface.Interface):
    """A File."""


class IPeerFactory(interface.Interface):
    """An object can make peer classes."""

    def make():
        """
        create a peer class, with a mapper, returns the mapped orm class
        """


class IPeerRegistry(interface.Interface):
    """ a registry mapping a content class to its orm peer class """

########################################
## Interface Specifications for AT Fields
########################################

class IComputedField(interface.Interface):
    """Archetypes Computed Field"""


class IStringField(interface.Interface):
    """Archetypes String Field"""


class IBooleanField(interface.Interface):
    """Archetypes Boolean Field"""


class IIntegerField(interface.Interface):
    """Archetypes Integer Field"""


class IFloatField(interface.Interface):
    """Archetypes Float Field"""


class IFixedPointField(interface.Interface):
    """Archetypes Fixed Point Field"""


class IReferenceField(interface.Interface):
    """Archetypes Reference Field """


class ILinesField(interface.Interface):
    """Archetypes Lines Field """


class IFileField(interface.Interface):
    """Archetypes Field Field """


class IImageField(interface.Interface):
    """Archetypes Image Field """


class IPhotoField(interface.Interface):
    """Archetypes Photo Field """


class ITextField(interface.Interface):
    """Archetypes Text Field """


class IDateTimeField(interface.Interface):
    """Archetypes DateTime Field """


class IDisplayList(interface.Interface):
    """Archetypes Vocabulary Display List """
