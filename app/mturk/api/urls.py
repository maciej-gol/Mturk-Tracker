from tenclouds.crud import urls as crud_urls

from django.conf.urls.defaults import patterns, url, include

from resources import HitGroupContentSearchResource, HitGroupContentResource

urlpatterns = patterns('',
    url(r'^', include(crud_urls.patterns(resource=HitGroupContentResource()))),
    url(r'^', include(crud_urls.patterns(resource=HitGroupContentSearchResource()))),
)
