from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('',
    url(r'^$', 'mturk.classification.views.aggregates',
        name='classification'),
    url(r'^aggregates/(?P<classes>\d+)/$', 
        'mturk.classification.views.aggregates',
        name='classification_aggregates'),
    url(r'^report/(?P<classes>\d+)/$', 
        'mturk.classification.views.report',
        name='classification_report'),
)
