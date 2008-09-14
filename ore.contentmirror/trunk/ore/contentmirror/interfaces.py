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

class IMirrored( interface.Interface ):
    """ marker interface, signifying that the content should be mirrored to a database """

# Base Generic Interface to Attach Default Adapters to    
try:
    from Product.Archetypes.interfaces import IBaseContent as IPortalContent
except:
    class IPortalContent( interface.Interface ): pass

class IMetaData( interface.Interface ):
    """ marker interface for sqlalchemy metadata, to allow for use in adaptation """


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
# Runtime Serialization
#########################################
      
class IOperation( interface.Interface ):

    oid = schema.ASCIILine( description=u"The identifier for the content" )
    filtered = schema.Bool( description=u"set by a filter to denote the opertion should be skipped")
    
    def process( connection ):
        """
        process an index operation
        """
        
class IFilter( interface.Interface ):
    """ a subscription adapter that can filter objects serialized"""

class IDeleteOperation( IOperation ): pass
class IUpdateOperation( IOperation ): pass
class IAddOperation( IOperation ): pass       

class IOperationBuffer( interface.Interface ):
    """ transactional operation buffer """

class IOperationFactory( interface.Interface ):
        """ """

class ISerializer( interface.Interface ):

    def add( ):
        """
        add the object to the database
        """
        
    def delete( ):
        """
        delete the object from the database
        """
        
    def delete( ):
        """
        delete the object from the database
        """

########################################    
## Schema Generation
########################################
class IModelLoader( interface.Interface ):
    
    def load( klass ):
        """ load a content class"""
        
    def transform( ):
        """ return a """
        
    def peer( transformer ):
        """ generate a content peer class for the content class """
        
# class ISchemaGenerator( interface.Interface ):
#     """ generates an rdb schema for a given class (an instance is passed)"""
#     metadata = interface.Attribute("metadata")
# 
#     def make( ):
#         """
#         """
# 
        
class ISchemaTransformer( interface.Interface ):
    """ translate an archetypes schema to a relational schema """
    
    metadata = interface.Attribute("metadata")
    
    def transform( ):
        """
        """
        
class IFieldTransformer(interface.Interface):
    """ """
    
    def transform( ):
        """
        """
        
    def copy( instance, peer ):
        """
        """
########################################    
## Content Peers
########################################
#         
class IContentPeer( interface.Interface ):
    """ a rdb persisted class that has a mirror of attributes of a portal content class"""

    transformer = schema.Object( ISchemaTransformer )
    
class IContentFile( interface.Interface ):
    pass

class IPeerFactory( interface.Interface ):
    """ """
    def make( ):
        """
        create a peer class, with a mapper
        """
        
class IPeerRegistry( interface.Interface ):
    """ """
    
########################################    
## Interface Specifications for AT Fields
######################################## 

class IComputedField( interface.Interface): pass
class IStringField( interface.Interface ): pass
class IBooleanField( interface.Interface ): pass   
class IIntegerField( interface.Interface ): pass
class IFloatField( interface.Interface ): pass
class IReferenceField( interface.Interface): pass
class ILinesField( interface.Interface ): pass
class IFileField( interface.Interface ): pass
class IImageField( interface.Interface ): pass
class IPhotoField( interface.Interface ): pass
class ITextField( interface.Interface ): pass
class IDateTimeField( interface.Interface ): pass
    
