------------
ore.rescueme
------------

A facility for mirroring the content of a Plone site into a structured
external datastore. Primarily, it focuses and supports out of the box,
content deployment to a relational database. The current
implementation provides for synchronous content mirroring or full site
copies. In synchronous mode, it updates the external store, as changes
are happening in Plone, and is integrated with the zope transaction 
machinery.

It allows the access of content from your Plone site in a language
and platform neutral manner.

It generically handles any archetypes content, with support for all
archetype field types, as well as serializing containment information.
Reference support does not support content or stateful based references objects.

Features
--------

 - Supports Any Archetypes Content ( including all Default Plone Content Types )
 - Completely Automated Mirroring, zero configuration required beyond initial db setup.
 - Supports Archetypes References, and Containment in the serialized database.
 - Frees content from Plone, useable by any syste
 - Easy customization via the Zope Component Architecture
 - Opensource ( GPLv3 )
 - Commercially Supported ( ObjectRealms )
 
Installation
------------

 see install.txt 
  
Boostrapping
------------

To demonstrate the system, let's create a custom archetype content
type and an instance of it. We'll add the marker interface IMirrored,
to get the mirror package's default component registrations. In
practice, we typically apply this interface via a zcml implements
directive to third party components.

  >>> import zope.interface, datetime
  >>> from ore.rescueme import interfaces
  >>> class MyPage( BaseContent ):
  ...     portal_type = 'My Page'
  ...     zope.interface.implements( interfaces.IMirrored )
  ...     schema = Schema(( 
  ...                StringField('title'),   
  ...                StringField('slug', required=True),   
  ...                IntegerField('days'), 
  ...                LinesField('people'),
  ...                DateTimeField('discovered_date')
  ...     ))
 
  >>> content = MyPage('front-page', title="The Cloud Apps", slug="Miracle Cures for Scaling")
  >>> content.title = u"FooBar"  
  >>> content.discovered_date = DateTime() # now
  >>> content.people = ["venkat", "tyrell", "johan", "arjun", "smithfield"]
  
Schema Tranformation
--------------------

In order to serialize content to a relational database, we need to
tranform our Archeypes schema to a relational database table. The package
provides sensible default FieldTransformers for all builtin Archetypes fields. 

First let's grab the sqlalchemy metadata structure to store our tables in

  >>> from ore.rescueme.schema import metadata
  
Now let's perform the transformation. 

  >>> from ore.rescueme import transform
  >>> transformer = transform.SchemaTransformer( content, metadata)
  >>> table = transformer.transform()
  >>> for column in table.columns: print column, column.type
    mypage.content_id Integer()
    mypage.slug Text(length=None, convert_unicode=False, assert_unicode=None)
    mypage.days Integer()
    mypage.people Text(length=None, convert_unicode=False, assert_unicode=None)
    mypage.discovered_date DateTime(timezone=False)

The default implementation of the ISchemaTransformer uses a common content 
table, to model common fields like dublin core attributes which are common to
all content.

Peers
-----

In order to utilize SQLAlchemy's ORM, we create a orm mapped class for
each content class. We call such sql persisted classes a peer. Using a
peer class allows us to serialize state to a relational database
without writing any SQL by hand. We can have the system create a peer
class for us, by using the peer factory.

  >>> from ore.rescueme import peer
  >>> factory = peer.PeerFactory( content, transformer )
  >>> peer_class = factory.make()
  >>> peer_class
  <class 'ore.rescueme.peer.MyPagePeer'>  

 
Model Loader
------------  

The model loader provides an abstraction for generating a relational
schema and a peer in high level interface. It looks up
ISchemaTransformer and IPeerFactory components.

  >>> from ore.rescueme.loader import loader
  >>> loader.load( MyPage )

If we attempt to load the same class twice a KeyError is raised.
 
  >>> loader.load( MyPage )
  Traceback (most recent call last):
  ...
  KeyError: "Duplicate <class 'MyPage'>"
    

Event Stream
------------

In order to serialize content as changes are happening in the CMS, we
integrate into the application server's event stream and subscribe to
content events. A typical problem in Plone at least, is that redundant
operations and events are fairly common, as well outright spurious
events from facilities like portal_factory. To combat that we
aggregate events on transaction boundaries, and automatically collapse
multiple operations for the same object.

To process the event stream, first we need to setup the database 
connection, and database table structure

  >>> import sqlalchemy as rdb
  >>> metadata.bind = rdb.create_engine('sqlite://')
  >>> metadata.create_all()
  

Operation Factories
-------------------

The event subscribers delegate to an operation factory, which provides
for creating deferred operations objects analagous to the Command
pattern.

For the runtime mirroring system, the operation factory provides a
critical policy point for customizing the behavior of content
mirroring. Providing a different operation factory, could be utilized
for deploying content to an xml database, or subversion content store,
or portal audit logs and BI reports. The default operation factory
tackles the relational mirroring problem domain. It provides
operations that process various content lifecycle events.

  >>> from ore.rescueme import operation
  >>> ops = operation.OperationFactory( content )
  
We can confirm that multiple operations automatically collapse to the
minimal set

  >>> ops.add()
  >>> list(operation.get_buffer())
  [<ore.rescueme.operation.AddOperation object at ...>]
  
If we delete the content in the same transaction scope, then
effectively for the purposes of mirroring, the content was never
created, and the buffer automatically removes any pending operations
for the content.
  
  >>> ops.delete()
  >>> operation.get_buffer().get( content.UID() )
  
  >>> ops.add()
  >>> ops.update()
  >>> operation.get_buffer().get( content.UID() )
  <ore.rescueme.operation.AddOperation object at ...>

Items in the buffer are automatically processed at transaction boundaries, if we
commit the transaction all operations held in the buffer are processed.

  >>> import transaction
  >>> transaction.get().commit()
  >>> list(operation.get_buffer())
  [] 

Alternatively if the transaction is aborted, all operations are discarded.

  >>> content.title = u"Shall Not Pass"
  >>> ops.update()
  >>> transaction.get().abort()
  >>> list(operation.get_buffer())
  []

Let's go ahead and process an update operation for test coverage...

  >>> ops.update()
  >>> transaction.get().commit()

Let's also exercise the delete operation to reset the database state
for other tests.

  >>> ops.delete()
  >>> transaction.get().commit()


Filters
-------

Sometimes we have content that we don't to mirror to the external
datastore. For example in Plone, Archetypes content is often created
inside the Portal Factory machinery, which creates objects in
temporary containers. This content is not persistent, and often has
partial state, nevertheless object lifecycle events are sent out for
it. The system uses a filter in its default configuration, to
automatically suppress processing of any content in portal factory.

Filters are modeled as subscription adapters, meaning each filter
matching against the context and operation, is applied in turn.

Let's create a simple filter that filters all content. We do this by
setting the filtered attribute of the operation, to True.

  >>> def content_filter( content, operation ):
  ...     operation.filtered = True
   
And let's register our filter with the component architecture.

  >>> from zope import component
  >>> component.provideSubscriptionAdapter( 
  ...      content_filter,
  ... 	   (interfaces.IMirrored, interfaces.IOperation ),
  ...      interfaces.IFilter )

Now if we try create an operation for the content, it will automatically
be filtered.
 
  >>> ops.add()
  >>> list(operation.get_buffer())
  []

Finally, let's remove the filter for other tests.

  >>> component.getSiteManager().unregisterSubscriptionAdapter( 
  ...    content_filter, 
  ... 	   (interfaces.IMirrored, interfaces.IOperation ),
  ...      interfaces.IFilter )
  True

Serializer
----------

Operations in turn delegate to a serializer. Serializers are
responsible for persisting the state of the object. They utilize the
content's peer to effect this. Peers are looked up via a peer registry
utility.  Schema transformers are used to copy the content's fields
state to the peer.

To demonstrate the serializer, first we need to register the peer
class with the registry.

  >>> from ore.rescueme import interfaces
  >>> registry = component.getUtility( interfaces.IPeerRegistry )
  >>> registry[ MyPage ] = peer_class

Now we can utilize the serializer directly to serialize our content to the
database.

  >>> from ore.rescueme import serializer
  >>> content_serializer = serializer.Serializer( content )
  >>> peer = content_serializer.add()
  >>> peer.slug
  'Miracle Cures for Scaling'

We can directly check the database to see the serialized content there.

  >>> import sqlalchemy as rdb
  >>> from ore.alchemist import Session
  >>> session = Session()
  >>> session.flush()
  >>> list(rdb.select( [table.c.content_id, table.c.slug] ).execute())
  [(1, u'Miracle Cures for Scaling')]

Serializers are also responsible for updating database respresentations. 

  >>> content.slug = "Find a home in the clouds"
  >>> peer = content_serializer.update()
  >>> peer.slug
  'Find a home in the clouds'

and deleting them.

  >>> session.flush()
  >>> content_serializer.delete()
  >>> list(rdb.select( [table.c.content_id, table.c.slug] ).execute())
  []

Due to the possibility of being installed and working with existing
content all the methods need to be reentrant. For example deleting 
non existent content shouldn't cause an exception.

  >>> content_serializer.delete()

or attempting to update content which does not exist, should in turn add it.

  >>> peer = content_serializer.update()
  >>> session.flush()
  >>> list(rdb.select( [table.c.content_id, table.c.slug] ).execute())
  [(1, u'Find a home in the clouds')]


Containment
-----------

Content in a plone portal is contained within the portal, and has explicit containment structure based on access (Acquisition). ie. Content is contained within folders, and folders are content. The contentmirror system captures this containment structure in the database serialization using the adjancey list support in SQLAlchemy.

To demonstrate, let's create a folderish content type and initialize it with the mirroring system.

  >>> class Folder( BaseContent ):
  ...     portal_type = 'Simple Folder'
  ...     zope.interface.implements( interfaces.IMirrored )
  ...     schema = Schema((
  ...                StringField('name'),   
  ...                StringField('slug', required=True),   
  ...                ReferenceField('related', relationship='inkind'), 
  ...                DateTimeField('discovered_date')
  ...     ))          

  >>> loader.load( Folder )
  >>> metadata.create_all(checkfirst=True)
  >>> root = Folder('root', name="Root")
  >>> subfolder = Folder('subfolder', name="SubOne", container=root)
  >>> peer = interfaces.ISerializer( subfolder ).add()
  >>> peer.parent.name == "Root"
  True
  >>> transaction.abort()
  
The content mirror automatically serializes a content's container if its not already serialized. Containment serialization is a recursive operation. In the course of normal operations, this has a nominal cost, as a 
the container would already have been serialized. Nonetheless, a common scenario when starting to use content mirror on an existing system is that content will be added to a container thats not serialized. Additionally, the container will have have been the subject of an object modified event, when a content object is added to it, leading to redundant serialization operations. The content mirror automatically detects and handles this.
 
Let's try loading this chain of objects through the operations factory, to demonstrate, with an additional update event for the container modification event.

  >>> operation.OperationFactory( root ).update()
  >>> operation.OperationFactory( subfolder ).add()
  >>> transaction.commit()
  
And let's load the subfolder peer from the database and verify its contained in the "root" folder

  >>> from ore.rescueme import schema
  >>> schema.fromUID( subfolder.UID() ).parent.name
  u'Root'

A caveat to using containment, is that filtering containers, will cause contained content to appear as orphans.

References
----------

Archetypes references are a topic onto themselves

  >>> class MyAsset( BaseContent ):
  ...     portal_type = "My Asset"
  ...     zope.interface.implements( interfaces.IMirrored )
  ...     schema = Schema((
  ...                StringField('name'),   
  ...                StringField('slug', required=True),   
  ...                ReferenceField('related', relationship='inkind'), 
  ...                DateTimeField('discovered_date')
  ...     ))

And setup the peers and database tables for our new content class.

  >>> loader.load( MyAsset )
  >>> metadata.create_all(checkfirst=True)
  >>> table = component.getUtility( interfaces.IPeerRegistry )[ MyAsset ].transformer.table
  >>> for column in table.columns: print column, column.type
    myasset.content_id Integer()
    myasset.name Text(length=None, convert_unicode=False, assert_unicode=None)
    myasset.slug Text(length=None, convert_unicode=False, assert_unicode=None)
    myasset.discovered_date DateTime(timezone=False)


Let's create some related content.

  >>> xo_image = MyAsset('xo-image', name="Icon")
  >>> logo = MyAsset('logo', name="Logo")
  >>> xo_article = MyAsset('xo-article', name='Article', related=xo_image )
  >>> home_page = MyAsset( 'home-page', related=[xo_article, logo] )  

And serialze the content

  >>> peer = interfaces.ISerializer( home_page ).add()

Related objects are accessible from the peer as the relations collection attribute. 

  >>> for ob in peer.relations: print ob.target.name, ob.relationship
    Article inkind
    Logo inkind


Files
-----

File content is automatically stored in the content class's table as a
binary field by default, however custom FileTransform adapters can
store content to the file system easily.

Custom Types
------------

Any custom archetypes can easily be added in via a zcml declaration, as an example
this is the configuration to setup ATDocuments:

  <configure xmlns="http://namespaces.zope.org/zope"
	   xmlns:ore="http://namespaces.objectrealms.net/mirror"> 
    <ore:mirror content="Products.ATContentTypes.content.document.ATDocument" />
  </configure>

