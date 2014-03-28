from tenclouds.crud import urls as crud_urls

from django.conf.urls.defaults import patterns, url, include

from resources import HitGroupContentSearchResource, HitSearchResource

urlpatterns = patterns('',
    url(r'^', include(crud_urls.patterns(resource=HitGroupContentSearchResource()))),
    url(r'^', include(crud_urls.patterns(resource=HitSearchResource()))),
    url(r'^search/$', 'mturk.search.views.search', name='haystack_search'),
)
