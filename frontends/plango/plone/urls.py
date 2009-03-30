from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^images/(?P<id>.*)/$', 'plone.views.images'),
    (r'^search/$', 'plone.views.search'),
    (r'^$', 'plone.views.front_page'),
)
