from django.http import Http404
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.template import loader, RequestContext
from django.http import HttpResponse, HttpResponseRedirect

from plone.models.base import Content

class PloneResolverMiddleware(object):
    def process_response(self, request, response):
        if response.status_code != 404:
            return response # No need to check for a plone pages for non-404 responses.
        try:
            path = request.path_info
            path = path.split("/")
            base = None
            breadcrumbs = []
            for name in path:
                if name:
                    tmpbase = get_object_or_404(Content, id=name, container=base)
                    if tmpbase.status in ["published", None]:
                        # we'll ignore anything that isn't None (files, images), published (the rest)
                        base = tmpbase
                        breadcrumbs.append(tmpbase)
                    else:
                        # this gets caught down below
                        raise Http404    
            
            if not hasattr(base, "normalize_name"):
                return response
                
            base = getattr(base, base.normalize_name() + "s")
            t = loader.get_template(base.default_template_name())
            c = {
                "object": base, 
                "breadcrumbs": breadcrumbs 
            }
            c.update(**base.default_context())
            response = HttpResponse(t.render(RequestContext(request, c)))
            return response
            
        # Return the original response if any errors happened. Because this
        # is a middleware, we can't assume the errors will be caught elsewhere.
        except Http404:
            return response
        except:
            if settings.DEBUG:
                raise
            return response
