from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('mturk.toprequesters.views',
    url(r'^(?P<tab>\d+)/$', 'top_requesters', name='graphs_top_requesters'),
    url(r'^$', 'top_requesters', name='graphs_top_requesters'),
)
