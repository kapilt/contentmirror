#!/usr/bin/env python

import os
import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.webapp import template

from main import ATDocument, ATImage, ATNewsItem

class CreateHandler(webapp.RequestHandler):

    def get(self):
        if users.get_current_user():
          url = users.create_logout_url(self.request.uri)
          url_linktext = 'Logout'
        else:
          url = users.create_login_url(self.request.uri)
          url_linktext = 'Login'

        template_values = {
          'type': self.request.get('type'),
          'url': url,
          'url_linktext': url_linktext,
        }

        path = os.path.join(os.path.dirname(__file__), 'create.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):
        type = self.request.get('type')
        if type=='atimage':
            content = ATImage()
            content.image = self.request.get('image')
            content.portal_type="Image"
        elif type=='atnewsitem':
            content = ATNewsItem()
            content.text = self.request.get('text')
            content.portal_type="News Item"
        else:
            content = ATDocument()
            content.text = self.request.get('text')
            content.portal_type="Document"
        content.id = self.request.get('id')
        content.title = self.request.get('title')
        content.description = self.request.get('description')
        content.creators = [users.get_current_user()]
        content.put()
        self.redirect('/')

def main():
    application = webapp.WSGIApplication([('/create', CreateHandler)],
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()
