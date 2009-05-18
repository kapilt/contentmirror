mirror.async
------------

Mirror async is the secret sauce! The default content mirror cannot
perform very much work when serializing content, as it is synchronous
to the request, ie. if it takes too long the end user must wait for
the server to respond while the work is being done. So the default
mirror is designed to do minimal work and have minimal performance
impact (1%-2%) on average, but hitting worst case scenario on large
file uploads (as does plone). Mirror async pushes the content mirror
operations to an external message bus. A separate zeo client polls and
processes the message bus and then processes the operations. This
allows us to do anything imaginable with the content, for example
serializing files to disk, upload content to app engine, transforming
and indexing into solr, pushing content to multiple databases.

transports
----------

Mirror async supports multiple message queue implementations, the core
abstraction interface that must be implemented is ITransport which has
methods for publishing, and polling messages from the message queue.

the three default async transport implementations are for AMQP (
http://en.wikipedia.org/wiki/Advanced_Message_Queuing_Protocol ) for
sites requiring local installations, control, high performance, and
enterprise level messaging features, Amazon SQS for sites needing a
robust and easy installation, and a relational database queue for ease
of installation but also requiring reliable database setup.

  >>> from mirror.async.interfaces import ITransport
  >>> from ore.contentmirror import interfaces, schema
  >>> import transaction, os
  >>> import sqlalchemy as rdb
  >>> from zope import component, interface

amqp
====

Let's create an AMQP Transport and register it as a transport for
content mirror operations. For testing portability and ease, we
utilize a fake implementation of amqp, the real implementation
can be used by setting up the environment variables as documented
in testing.txt::
  
  >>> from mirror.async.amqp import AMQPTransport
  >>> amqp_transport = AMQPTransport( connection=_amqp_connection_ )
  >>> component.provideUtility( amqp_transport )
  
Now let's publish some content mirror operations to the remote message
bus. First we need to setup a content type for contentmirror::

  >>> class Page( BaseContent ):
  ...     portal_type = "Simple Type"
  ...     interface.implements( interfaces.IMirrored )
  ...     schema = Schema((
  ...         StringField('name'),   
  ...         StringField('slug', required=True),   
  ...         DateTimeField('discoveredDate')
  ...     ))

  >>> from ore.contentmirror.loader import loader
  >>> loader.load( Page )
  >>> db_url = os.environ.get('DATABASE_URL') or 'sqlite://'
  >>> schema.metadata.bind = rdb.create_engine( db_url )  
  >>> schema.metadata.create_all( checkfirst=True )
  >>> p = Page( "home-page", name="abc", slug="treaty" )


The main difference between the default contentmirror operation and
the async mode is that the transaction operation buffer implementation
changes to an async aware buffer, that will serialize the minimal set
of operations to the transport on transaction boundaries.

  >>> from ore.contentmirror import operation
  >>> operation.get_buffer()
  <mirror.async.operation.AsyncOperationBuffer object at ...>

Now let's push an operation through to the transport.
  
  >>> ops = operation.OperationFactory( p )
  >>> ops.add()
  >>> transaction.commit()
  >>> _amqp_connection_.__class__ == 'FakeAMQP' and len(_amqp_connection_.get_channel().messages) or 1
  1

amazon sqs
==========

Now let's test the Amazon SQS implementation

  >>> from mirror.async.sqs import SQSTransport
  >>> sqs_transport = SQSTransport( connection=_sqs_connection_ )
  >>> component.getGlobalSiteManager().unregisterUtility( provided=ITransport )
  True
  >>> component.provideUtility( sqs_transport )

and push the operation through to the transport

  >>> ops = operation.OperationFactory( p )
  >>> ops.add()
  >>> transaction.commit()
  >>> _sqs_connection_.__class__ == 'FakeSQS' and len(_sqs_connection_.get_channel().messages) or 1
  1

pros 
 - very easy to setup 

cons
 - requires low latency, reliable internet connection
 - minimal information disclosure (albeit over ssl)
 - reliance on third party

rdb queue
=========

The relational queue implementation, utilizes a relational database table to store operations for the 
async processor. one limitation of using an relational table is that we can only utilize one processor
at a time, where as the true message bus implementations can support multiple processors. otoh, 
its a relatively straightforward installation from a default content mirror setup, as we'll eventually
be persisting the content to a relational database.

  >>> from mirror.async.rdb import RDBTransport, message_queue as rdb_queue
  >>> schema.metadata.create_all(checkfirst=True)
  >>> rdb_transport = RDBTransport()
  >>> component.getGlobalSiteManager().unregisterUtility( provided=ITransport )
  True
  >>> component.provideUtility( rdb_transport )

and push the operation through to the transport

  >>> ops = operation.OperationFactory( p )
  >>> ops.add()
  >>> transaction.commit()
  >>> len(list(rdb_queue.select().execute()))
  1

pros
++++
 - easy to setup
 
cons
++++

 - requires database connection pool from each plone zeo client.
 - requires only one operation processor active.
 - database must be operational

processor
---------

once the operations have been delivered to a transport, we utilize a zeo client as a subscriber to the
various messages. The transport component provides the required support for receiving messages from
the message bus. First let's setup the zeo client processor::

  >>> from mirror.async import processor
  >>> db = open_zodb( p )
  >>> async_processor = processor.AsyncProcessor( db, '/Plone', sqs_transport )
  
next process the events
 
  >>> async_processor()
  
And check the database for the stored content::

  >>> results = list(schema.content.select().execute())
  >>> len(results)
  1
  >>> results[0].id
  u'home-page'
  >>> clear_db() # remove all content in the database
  
Let's try the same with the amqp transport


  
The amqp transport has different modes based on whether its publish or subscribe mode, typically this usage
isn't needed as we have different processes for each, but for testing we reset the transport, before activating
the processor to enable the transport to go into subscribe mode.
  
  >>> amqp_transport.reset() 
  
  >>> async_processor = processor.AsyncProcessor( db, '/Plone', amqp_transport )  
  >>> async_processor()
  >>> results = list(schema.content.select().execute())
  >>> len(results)
  1
  >>> results[0].id
  u'home-page'
  >>> clear_db() # remove all content in the database  
  
Lastly the relational database implementation, because we've been clearing the database
we need to repopulate the rdb queue first.

  >>> ops = operation.OperationFactory( p )
  >>> ops.add()
  >>> transaction.commit()

  >>> async_processor = processor.AsyncProcessor( db, '/Plone', rdb_transport )  
  >>> async_processor()
    
  >>> results = list(schema.content.select().execute())
  >>> len(results)
  1
  >>> results[0].id
  u'home-page'

Verify the rdb queue table is now empty

  >>> len( list( rdb_queue.select().execute()))
  0
  

    
 