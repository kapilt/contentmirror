----------
mirror.gae
----------

This code is based on the ContentMirror product by Kapil Thangavelu.

mirror.gae is a facility for mirroring the content of a Plone site into a Google 
App Engine datastore. Primarily, it focuses and supports out of the box,
content deployment to Google App Engine. The current
implementation provides for synchronous content mirroring or full site
copies. In synchronous mode, it updates the external store, as changes
are happening in Plone, and is integrated with the zope transaction
machinery.

Features
--------

 - Out of the Box support for Default Plone Content Types.
 - Out of the Box support for all builtin Archetypes Fields (including files, and references ).
 - Will support Any 3rd Party / Custom Archetypes Content.
 - Supports Capturing Containment / Content hierarchy in the serialized database. 
 - Completely Automated Mirroring, zero configuration required beyond installation.
 - Easy customization via the Zope Component Architecture
 - Opensource ( GPLv3 )
 - Support for Plone 2.5, 3.0, and 3.1

Installation
------------

 see install.txt
  

