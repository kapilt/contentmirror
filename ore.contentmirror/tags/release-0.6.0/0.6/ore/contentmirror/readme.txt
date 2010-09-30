-----------------
ore.contentmirror
-----------------

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
Reference support does not support content or stateful based
references objects.

Features
--------

 - Out of the Box support for Default Plone Content Types.
 - Out of the Box support for all builtin Archetypes Fields (including files, and references ).
 - Supports Any 3rd Party / Custom Archetypes Content.
 - Supports Capturing Containment / Content hierarchy in the serialized database.
 - Completely Automated Mirroring, zero configuration required beyond installation.
 - Easy customization via the Zope Component Architecture
 - Opensource ( GPLv3 )
 - Elegant and Simple Design, less than 600 lines of code, 100% unit test coverage.
 - Support for Plone 2.5, 3.0, and 3.1
 - Commercial Support Available ( ObjectRealms )

Installation
------------

 see install.txt

Bootstrapping
------------

To demonstrate the system, let's create a custom archetype content
type and an instance of it. We'll add the marker interface IMirrored,
to get the mirror package's default component registrations. In
practice, we typically apply this interface via a zcml implements
directive to third party components::

  >>> import zope.interface
  >>> from datetime import datetime
  >>> from ore.contentmirror import interfaces
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

  >>> content = MyPage('front-page', title="The Cloud Apps", slug="Miracle Cures for Rabbits")
  >>> content.title = u"FooBar"
  >>> content.discovered_date = DateTime() # now
  >>> content.people = ["venkat", "tyrell", "johan", "arjun", "smithfield"]

Note on Examples
----------------

For testing purposes a mock implementation was constructed to avoid
the need for setting up a Plone instance for development. From the
perspective of the api used by contentmirror the machinery is
identical but the differences in for some attributes as done in these
examples differs from the actual plone api for doing the same.

Schema Tranformation
--------------------

In order to serialize content to a relational database, we need to
tranform our Archeypes schema to a relational database table. The package
provides sensible default FieldTransformers for all builtin Archetypes fields.

First let's grab the sqlalchemy metadata structure to store our tables in::

  >>> from ore.contentmirror.schema import metadata

Now let's perform the transformation::

  >>> from ore.contentmirror import transform
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
class for us, by using the peer factory::

  >>> from ore.contentmirror import peer
  >>> factory = peer.PeerFactory( content, transformer )
  >>> peer_class = factory.make()
  >>> peer_class
  <class 'ore.contentmirror.peer.MyPagePeer'>


Model Loader
------------

The model loader provides an abstraction for generating a relational
schema and a peer in high level interface. It looks up and utilizes
ISchemaTransformer and IPeerFactory components to load a content class
into the mirroring system::

  >>> from ore.contentmirror.loader import loader
  >>> loader.load( MyPage )

If we attempt to load the same class twice a KeyError is raised::

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
connection, and database table structure::

  >>> import os
  >>> import sqlalchemy as rdb
  >>> metadata.bind = rdb.create_engine(test_db_uri())
  >>> metadata.create_all(checkfirst=True)


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
operations that process various content lifecycle events::

  >>> from ore.contentmirror import operation
  >>> ops = operation.OperationFactory( content )

We can confirm that multiple operations automatically collapse to the
minimal set::

  >>> ops.add()
  >>> list(operation.get_buffer())
  [<ore.contentmirror.operation.AddOperation object at ...>]

If we delete the content in the same transaction scope, then
effectively for the purposes of mirroring, the content was never
created, and the buffer automatically removes any pending operations
for the content::

  >>> ops.delete()
  >>> operation.get_buffer().get( id(content) )

if we create an add operation, and an update operation in a single
transaction scope, it should collapse down to just the add operation::

  >>> ops.add()
  >>> ops.update()
  >>> operation.get_buffer().get( id(content) )
  <ore.contentmirror.operation.AddOperation object at ...>

if we have modified the object's uid in the same transaction we should
have still one operation for the object::

  >>> len(list(operation.get_buffer()))
  1
  >>> from ore.contentmirror.tests.base import make_uuid
  >>> content.uid = make_uuid(content.id)
  >>> ops.update()
  >>> len(list(operation.get_buffer()))
  1


Operations in the transaction buffer are automatically processed at
transaction boundaries, if we commit the transaction all operations
held in the buffer are processed::

  >>> import transaction
  >>> transaction.get().commit()
  >>> list(operation.get_buffer())
  []

Alternatively if the transaction is aborted, all operations are discarded::

  >>> content.title = u"Shall Not Pass"
  >>> ops.update()
  >>> transaction.get().abort()
  >>> list(operation.get_buffer())
  []

Let's go ahead and process an update operation for test coverage::

  >>> ops.update()
  >>> transaction.get().commit()

Let's also exercise the delete operation to reset the database state
for other tests::

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
setting the filtered attribute of the operation, to True::

  >>> def content_filter( content, operation ):
  ...     operation.filtered = True

And let's register our filter with the component architecture::

  >>> from zope import component
  >>> component.provideSubscriptionAdapter(
  ...      content_filter,
  ...      (interfaces.IMirrored, interfaces.IOperation ),
  ...      interfaces.IFilter )

Now if we try create an operation for the content, it will automatically
be filtered::

  >>> ops.add()
  >>> list(operation.get_buffer())
  []

Finally, let's remove the filter for other tests::

  >>> component.getSiteManager().unregisterSubscriptionAdapter(
  ...    content_filter,
  ...    (interfaces.IMirrored, interfaces.IOperation ),
  ...    interfaces.IFilter )
  True

Serializer
----------

Operations in turn delegate to a serializer. Serializers are
responsible for persisting the state of the object. They utilize the
content's peer to effect this. Peers are looked up via a peer registry
utility.  Schema transformers are used to copy the content's fields
state to the peer.

To demonstrate the serializer, first we need to register the peer
class with the registry::

  >>> from ore.contentmirror import interfaces
  >>> registry = component.getUtility( interfaces.IPeerRegistry )
  >>> registry[ MyPage ] = peer_class

Now we can utilize the serializer directly to serialize our content to the
database::

  >>> from ore.contentmirror import serializer
  >>> content_serializer = serializer.Serializer( content )
  >>> peer = content_serializer.add()
  >>> peer.slug
  'Miracle Cures for Rabbits'

We can directly check the database to see the serialized content there::

  >>> import sqlalchemy as rdb
  >>> from ore.contentmirror.session import Session
  >>> session = Session()
  >>> session.flush()
  >>> list(rdb.select( [table.c.content_id, table.c.slug] ).execute())
  [(..., u'Miracle Cures for Rabbits')]

Serializers are also responsible for updating database respresentations::

  >>> content.slug = "Find a home in the clouds"
  >>> peer = content_serializer.update()
  >>> peer.slug
  'Find a home in the clouds'

and deleting them::

  >>> session.flush()
  >>> content_serializer.delete()
  >>> list(rdb.select( [table.c.content_id, table.c.slug] ).execute())
  []

Due to the possibility of being installed and working with existing
content all the methods need to be reentrant. For example deleting
non existent content shouldn't cause an exception::

  >>> content_serializer.delete()

or attempting to update content which does not exist, should in turn add it::

  >>> peer = content_serializer.update()
  >>> session.flush()
  >>> list(rdb.select( [table.c.content_id, table.c.slug] ).execute())
  [(..., u'Find a home in the clouds')]


Containment
-----------

Content in a plone portal is contained within the portal, and has
explicit containment structure based on access (Acquisition).
ie. Content is contained within folders, and folders are content. The
contentmirror system captures this containment structure in the
database serialization using the adjancey list support in SQLAlchemy.

To demonstrate, let's create a folderish content type and initialize
it with the mirroring system::

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

The content mirror automatically serializes a content's container if
its not already serialized. Containment serialization is a recursive
operation. In the course of normal operations, this has a nominal
cost, as the content's container would already have been serialized,
from a previous add event.

Nonetheless, a common scenario when starting to use content mirror on
an existing system is that content will be added to a container thats
not been serialized, in which case the serialization will recurse till
it has captured the entire parent chain. When operating on existing
systems, its best to let the content mirroring process 'catch up', by
running the bulk serialization tool as documented in the installation
file. Once this tools has been run, containment operation recursion is
minimal.
 
Additionally, when adding content to a container, the container will
have have been the subject of an object modified event, when a content
object is added to it, leading to redundant serialization
operations. The content mirror automatically detects and handles this.
 
Let's try loading this chain of objects through the operations
factory, to demonstrate, with an additional update event for the
container modification event::

  >>> operation.OperationFactory( root ).update()
  >>> operation.OperationFactory( subfolder ).add()
  >>> transaction.commit()
  
And let's load the subfolder peer from the database and verify its
contained in the "root" folder::

  >>> from ore.contentmirror import schema
  >>> schema.fromUID( subfolder.UID() ).parent.name
  u'Root'

A caveat to using containment, is that filtering containers, will
cause contained mirrored content to appear as orphans/root objects.


Containment hiearchies can be queried either via the adjancency tree model using
join depth to control the number of levels fetched in a single query, or via
a path prefix query against the portal relative path on a content node.
 
  >>> schema.fromUID( subfolder.UID() ).path
  u'root/subfolder'

Delete operations on a container, cascade down to all contained content.
Test note, demonstrating this requires usage of a database with foreign key action
support ( for cascade operators ), but the default test database is sqlite
so we won't attempt verification.
 
  >>> operation.OperationFactory( root ).delete()
  >>> transaction.commit()

Workflow
--------

A content's workflow status is also captured in the database. the state are evident below
as we construct some sample content to serialize the state::

   >>> my_space = Folder("my-space")
   >>> my_space.workflow_state = "archived"
   >>> peer = interfaces.ISerializer( my_space ).add()
   >>> peer.status
   'archived'

References
----------

Archetypes references are a topic onto themselves. By default,
References got stored in a relation table which containing the source
and target content ids, and a relationship name. Let's create a
content class with reference fields to demonstrate::

  >>> class MyAsset( BaseContent ):
  ...     portal_type = "My Asset"
  ...     zope.interface.implements( interfaces.IMirrored )
  ...     schema = Schema((
  ...                StringField('name'),   
  ...                StringField('slug', required=True),   
  ...                ReferenceField('related', relationship='inkind'), 
  ...                DateTimeField('discoveredDate')
  ...     ))

And setup the peers and database tables for our new content class::

  >>> loader.load( MyAsset )
  >>> metadata.create_all(checkfirst=True)
  >>> table = component.getUtility( interfaces.IPeerRegistry )[ MyAsset ].transformer.table
  >>> for column in table.columns: print column, column.type
    myasset.content_id Integer()
    myasset.name Text(length=None, convert_unicode=False, assert_unicode=None)
    myasset.slug Text(length=None, convert_unicode=False, assert_unicode=None)
    myasset.discovereddate DateTime(timezone=False)

Let's create some related content::

  >>> xo_image = MyAsset('xo-image', name="Icon")
  >>> logo = MyAsset('logo', name="Logo")
  >>> xo_article = MyAsset('xo-article', name='Article', related=xo_image, discoveredDate=DateTime() )
  >>> home_page = MyAsset( 'home-page', related=[xo_article, logo] )  

And serialze the content. Any objects referenced by a serialized
object are also serialized if they not have already been
serialized. In this way reference processing like containment, is
recursive::

  >>> peer = interfaces.ISerializer( home_page ).add()
  
Related objects are accessible from the peer as the relations
collection attribute::

  >>> for ob in peer.relations: print ob.target.name, ob.relationship
    Article inkind
    Logo inkind

If we modify a content object, its references are not serialized
again::

  >>> session.flush()
  >>> home_page.title = "Home"
  >>> peer = interfaces.ISerializer( home_page ).update()
  >>> session.dirty
  IdentitySet([<ore.contentmirror.peer.MyAssetPeer object at ...>])
  
  >>> for ob in peer.relations: print ob.target.name, ob.relationship
    Article inkind
    Logo inkind

When performing case manipulation, let's verify that we're serializing the values properly.

  >>> schema.fromUID( xo_article.UID() ).discovereddate
  datetime.datetime(...)

Files
-----

File content is automatically stored in a separate files table, with
foreign key pointers back to the origin content. The files table uses
the binary field in sqlalchemy for storing content.

Let's demonstrate using the default file handling which stores files
into a database. First a class with a file field::

  >>> class ExampleContent( BaseContent ):
  ...     portal_type = "My File"
  ...     zope.interface.implements( interfaces.IMirrored )
  ...     schema = Schema((
  ...                StringField('Name'),   
  ...                FileField('file_content', required=True),   
  ...     ))
  >>> loader.load( ExampleContent )
  >>> metadata.create_all( checkfirst=True )
  
We can see that the sqlalchemy class mapper uses a relation property for the field::
  
  >>> from sqlalchemy import orm
  >>> peer_factory = component.getUtility( interfaces.IPeerRegistry )[ ExampleContent ]
  >>> mapper = orm.class_mapper( peer_factory )
  >>> mapper.get_property('file_content')
  <sqlalchemy.orm.properties.RelationProperty object at ...>
    
Let's create some content with files and serialize it::

  >>> image = ExampleContent('moon-image', Name="Icon", file_content=File("treatise.txt", "hello world") )
  >>> peer = interfaces.ISerializer( image ).add()
  >>> peer
  <ore.contentmirror.peer.ExampleContentPeer object at ...>
  >>> peer.name
  'Icon'
  >>> session.flush()   
  
Now let's verify the presence of the file in the files table:
  
  >>> list(rdb.select( [schema.files.c.file_name, schema.files.c.content, schema.files.c.checksum],
  ...      schema.files.c.content_id == peer.content_id).execute() )
  [(u'treatise.txt', <read-write buffer ptr ..., size 11 at ...>, u'5eb63bbbe01eeed093cb22bb8f5acdc3')]
  
If we modify it, what happens to the database during update::

  >>> image.file_content=File("treatise.txt", "hello world 2") 
  >>> peer = interfaces.ISerializer( image ).update()
  >>> peer.file_content
  <ore.contentmirror.schema.File object at ...>  

We'll end up with two dirty (modified) objects in the sqlalchemy session
corresponding to the content peer, and its file peer::
  
  >>> dirty = list(session.dirty)
  >>> dirty.sort()
  >>> dirty
  [<ore.contentmirror.peer.ExampleContentPeer object at ...>, <ore.contentmirror.schema.File object at ...>]
  
And if we flush the session, we can verify the updated contents of the database::
  
  >>> session.flush()   
  >>> list(rdb.select( [schema.files.c.file_name, schema.files.c.content, schema.files.c.checksum, ],
  ...      schema.files.c.content_id == peer.content_id).execute() )
  [(u'treatise.txt', <read-write buffer ptr ..., size 13 at ...>, u'5270941191198af2a01db3572f1b47e8')]
  
If we modify the object without modifying the file content, the file
content is not written to the database, a md5 checksum comparison is
made between the object file contents and the file peer checksum,
before modifying the file peer::

  >>> image.title = "rabbit"
  >>> peer = interfaces.ISerializer( image ).update()
  >>> session.dirty
  IdentitySet([<ore.contentmirror.peer.ExampleContentPeer object at ...>])
  
  
Reserved Words
--------------

Most databases have a variety of sql words reserved in their dialect,
the schema transformation takes this into account when generating
column names, and prefixes any reserved words with 'at'::

  >>> class ExamplePage( BaseContent ):
  ...     portal_type = 'My Page'
  ...     zope.interface.implements( interfaces.IMirrored )
  ...     schema = Schema(( 
  ...                StringField('begin'),   
  ...                StringField('end', required=True),   
  ...                IntegerField('commit'), 
  ...                LinesField('select'),
  ...                DateTimeField('where')
  ...     ))  
  >>> 
  >>> transformer = transform.SchemaTransformer( ExamplePage('a'), metadata)
  >>> table = transformer.transform()
  >>> for column in table.columns: print column, column.type
    examplepage.content_id Integer()
    examplepage.at_begin Text(length=None, convert_unicode=False, assert_unicode=None)
    examplepage.at_end Text(length=None, convert_unicode=False, assert_unicode=None)
    examplepage.at_commit Integer()    
    examplepage.at_select Text(length=None, convert_unicode=False, assert_unicode=None)
    examplepage.at_where DateTime(timezone=False)
  
Custom Types
------------

Any custom archetypes can easily be added in via a zcml declaration,
as an example this is the configuration to setup ATDocuments::

  <configure xmlns="http://namespaces.zope.org/zope"
             xmlns:ore="http://namespaces.objectrealms.net/mirror"> 
    <ore:mirror content="Products.ATContentTypes.content.document.ATDocument" />
  </configure>

Limitations
-----------

Undo is not supported as it directly relies on ZODB level features without
any application awareness. Content mirror relies on application level events
for proper functioning. Even in that case, Content mirror will become eventually
consistent with the ZODB state as application level events are triggered for
content affected by the Undo, the one exception to this is new content added,
that is removed by the Undo functionality of the ZODB. Typically on a Plone
site with active content creation, the utility of Undo is limited in practice.
There are no plans to address this at this time. If its of significant concern,
utilizing the serializer scripts in cron fashion instead of the synchronous
replication offered by the runtime might be more effective.


Development
-----------

The project homepage is http://contentmirror.googlecode.com which
contains links to documentation, issue trackers, code repositories, and
mailing lists.

Commercial Support
------------------

The contentmirror system is designed to be useable out of the box, but
if you need commercial support, please contact us at kapil.foss@gmail.com

Credits
-------
Kapil Thangavelu
Alan Runyan
Laurence Rowe
Tim Knapp
Wichert Akkerman



