from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import direct_to_template, redirect_to


urlpatterns = patterns('',
    url(r'^$', redirect_to, {'url': '/general/'}),
    url(r'^general/$', 'mturk.main.views.general', name='graphs_general'),
    url(r'^general/(?P<tab_slug>[\w-]+)/$', 'mturk.main.views.general',
        name='graphs_general'),

    url(r'^about/$', direct_to_template, {'template': 'main/about.html'},
        name='about'),

    url(r'^arrivals/$', 'mturk.main.views.arrivals', name='graphs_arrivals'),
    url(r'^arrivals/(?P<tab_slug>[\w-]+)/$', 'mturk.main.views.arrivals',
        name='graphs_arrivals'),

    url(r'^top_requesters/(?P<tab>\d+)/$', 'mturk.main.views.top_requesters',
        name='graphs_top_requesters'),
    url(r'^top_requesters/$', 'mturk.main.views.top_requesters',
        name='graphs_top_requesters'),

    url(r'^requester_details/(?P<requester_id>[A-Z0-9]+)/$',
        'mturk.main.views.requester_details', name='requester_details'),
    url(r'^hit/content/(?P<hit_group_id>[a-fA-Z0-9]+)/$',
        'mturk.main.views.hit_group_content', name='hit_group_content'),
    url(r'^hit/(?P<hit_group_id>[a-fA-Z0-9]+)/$',
        'mturk.main.views.hit_group_details', name='hit_group_details'),

    url(r'^admin/requester/status/toggle/(?P<id>[^/]*)/$',
        'mturk.main.admin.toggle_requester_status',
        name='admin-toggle-requester-status'),
    url(r'^admin/hitgroup/status/toggle/(?P<id>[^/]*)/$',
        'mturk.main.admin.toggle_hitgroup_status',
        name='admin-toggle-hitgroup-status'),
)
