from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from django.conf import settings
import os
this = settings.THIS_DIR

urlpatterns = patterns('',
    # Uncomment the next line to enable the admin:
    #(r'^admin/', include(admin.site.urls)),

    (r'^site-media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(this, 'media')}),
    (r'^', include('plone.urls')),
)
