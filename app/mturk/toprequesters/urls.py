from django.conf.urls.defaults import patterns, url, include
from tenclouds.crud import urls as crud_urls

from resources import ToprequestersResource


urlpatterns = patterns('mturk.toprequesters.views',
    url(r'', include(crud_urls.patterns(resource=ToprequestersResource()))),
    url(r'^(?P<tab>\d+)/$', 'top_requesters', name='graphs_top_requesters'),
    url(r'^$', 'top_requesters', name='graphs_top_requesters'),
)
