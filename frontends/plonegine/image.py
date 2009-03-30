import base64
import wsgiref.handlers

from google.appengine.ext import db
from google.appengine.ext import webapp

from main import ATImage

class DocumentHandler(webapp.RequestHandler):
  def get(self):
    id = self.request.path.split('/')[-1]
    content = ATImage.gql("where id=:1",id).fetch(1)
    if content:
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(content[0].image)
    else:
        self.error(404)

def main():
    application = webapp.WSGIApplication([('/image/.*', DocumentHandler)],
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()
