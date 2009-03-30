#!/usr/bin/env python

import os
import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.ext.db import polymodel
from google.appengine.api import users

class PloneContent(polymodel.PolyModel):
    id = db.StringProperty()
    uid = db.StringProperty()
    portal_type = db.StringProperty()
    status = db.StringProperty()
    type = db.StringProperty()
    path = db.StringProperty()
    title = db.StringProperty()
    description = db.StringProperty(multiline=True)
    subject = db.StringListProperty()
    location = db.StringListProperty()
    contributors = db.ListProperty(users.User)
    creators = db.ListProperty(users.User)
    creation_date = db.DateTimeProperty(auto_now_add=True)
    modification_date = db.DateTimeProperty(auto_now_add=True)
    effectivedate = db.DateTimeProperty(auto_now_add=True)
    expirationdate = db.DateTimeProperty()
    language = db.StringListProperty()
    rights = db.StringListProperty()
    container = db.ReferenceProperty()

class ATFolder(PloneContent):
    default_page = db.ReferenceProperty()

class ATBTreeFolder(PloneContent):
    default_page = db.ReferenceProperty()

class ATDocument(PloneContent):
    text = db.TextProperty()

class ATFavorite(PloneContent):
    remoteurl = db.StringProperty()

class ATLink(PloneContent):
    remoteurl = db.StringProperty()

class ATNewsItem(PloneContent):
    text = db.TextProperty()
    imagecaption = db.StringProperty(multiline=True)

class ATImage(PloneContent):
    image = db.BlobProperty()

class ATFile(PloneContent):
    file = db.BlobProperty()

class ATEvent(PloneContent):
    startdate = db.DateTimeProperty()
    enddate = db.DateTimeProperty()
    text = db.TextProperty()
    attendees = db.StringProperty()
    eventtype = db.StringProperty()
    eventurl = db.StringProperty()
    contactname = db.StringProperty()
    contactemail = db.StringProperty()
    contactphone = db.StringProperty()

class MainHandler(webapp.RequestHandler):

    def get(self):
        if users.get_current_user():
          url = users.create_logout_url(self.request.uri)
          url_linktext = 'Logout'
        else:
          url = users.create_login_url(self.request.uri)
          url_linktext = 'Login'

        content = db.GqlQuery("SELECT * from PloneContent ORDER BY modification_date DESC LIMIT 10")
        template_values = {
          'content': content,
          'url': url,
          'url_linktext': url_linktext,
        }

        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

def main():
    application = webapp.WSGIApplication([('/', MainHandler)],
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()
