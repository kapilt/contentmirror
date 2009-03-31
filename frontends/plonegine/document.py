import os
import wsgiref.handlers

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users

from main import ATDocument, PloneContent, ATImage
from main import class_for_portal_type

import traceback, logging
logging.getLogger().setLevel(logging.DEBUG)

class GenericDocumentHandler(webapp.RequestHandler):
    def get(self):
        logging.debug('got here')
        id = self.request.path.split('/')[-1] 
        # get the path based on the url
        path = self.request.path.replace("/document/", "")
        logging.debug("path="+path)
        # get the portal type based on the path
        plone_content = PloneContent.gql("where path=:1", path).fetch(1)
        if not plone_content:
            return self.error(404)
        logging.debug("id="+plone_content[0].id)
        # get the class based on the portal type
        class_obj = class_for_portal_type[plone_content[0].portal_type]
        # logging.debug("class_name="+class_name)
        # gql = "select * from %s where id=:1" % class_name
        # content = db.GqlQuery(gql, plone_content[0].id).fetch(1)
        content = class_obj.gql("where id=:1", plone_content[0].id).fetch(1)
        if content:
            if users.get_current_user():
              url = users.create_logout_url(self.request.uri)
              url_linktext = 'Logout'
            else:
              url = users.create_login_url(self.request.uri)
              url_linktext = 'Login'
            
            # convert the PolyModel object to a dict
            template_values = {}
            logging.debug(dir(content[0]))
            logging.debug(class_obj.properties())
            for key in class_obj.properties().keys():
                template_values[key] = getattr(content[0], key)
            
            template_values["contributors"] = ','.join(content[0].contributors)
            template_values["url"] = url
            template_values["url_linktext"] = url_linktext
            # template filename is based on the portal_type attribute
            template_name = 'templates/'+content[0].portal_type+'.html'
            template_path = os.path.join(os.path.dirname(__file__), template_name)
            logging.debug('template path='+path)
            self.response.out.write(template.render(template_path, template_values))
        else:
            self.error(404)

def main():
    application = webapp.WSGIApplication([('/document/.*', GenericDocumentHandler)],
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()
