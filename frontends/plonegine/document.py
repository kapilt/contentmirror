import os
import wsgiref.handlers

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users

from main import ATDocument

class ImageHandler(webapp.RequestHandler):
    def get(self):
        id = self.request.path.split('/')[-1]
        content = ATDocument.gql("where id=:1",id).fetch(1)
        if content:
            if users.get_current_user():
              url = users.create_logout_url(self.request.uri)
              url_linktext = 'Logout'
            else:
              url = users.create_login_url(self.request.uri)
              url_linktext = 'Login'
            template_values = {
              'title': content[0].title,
              'description': content[0].description,
              'modification_date': content[0].modification_date,
              'author': content[0].creators[0],
              'contributors': ','.join(content[0].contributors),
              'url': url,
              'url_linktext': url_linktext,
              'text': content[0].text,
            }
            path = os.path.join(os.path.dirname(__file__), 'document.html')
            self.response.out.write(template.render(path, template_values))
        else:
            self.error(404)

def main():
    application = webapp.WSGIApplication([('/document/.*', ImageHandler)],
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()
