------------------------
TALES String Field Tests
------------------------

These tests will test the TALES String field transform.

Bootstrapping
-------------
set up the same type of stuff in the readme.txt doctest

  >>> import zope.interface, os
  >>> from datetime import datetime

Testing Database environment variable setup

  >>> db_url = os.environ.get('CONTENTMIRROR_URI') or 'sqlite://'

This is the key that contentmirror expects to find its database
variable at

  >>> os.environ['CONTENTMIRROR_URI'] = db_url
  >>> import sqlalchemy as rdb
  >>> db = rdb.create_engine(db_url)

  >>> from ore.contentmirror import interfaces
  >>> from ore.contentmirror.schema import metadata
  >>> from ore.contentmirror.loader import loader
  >>> import transaction 

Lets confirm the TALES String field content will serialize across
to the RDBMS.

  >>> class TALESStringContent( BaseContent ):
  ...     portal_type = "TALESString Content"
  ...     zope.interface.implements( interfaces.IMirrored )
  ...     schema = Schema((
  ...         StringField('name'),   
  ...         StringField('slug', required=True),
  ...         TALESString('mytalesstring')   
  ...     ))
  >>> loader.load( TALESStringContent )
  >>> metadata.bind = db
  >>> metadata.drop_all(checkfirst=True)
  >>> metadata.create_all(checkfirst=True)
  >>> tales1 = TALESStringContent( 'purple-people-eater', name='Purple People Eaters', slug="They're big and purple", mytalesstring='string:Wow TAL code')
  >>> peer1 = interfaces.ISerializer( tales1 ).add()
  >>> transaction.commit()
