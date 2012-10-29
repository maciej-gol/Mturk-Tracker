from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.core.management import call_command

admin.autodiscover()


def bad(request):
    """ Simulates a server error """
    1 / 0

urlpatterns = patterns('mtracker',

    #url(r'^$', 'main.views.index', name='index'),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^documentation/$', 'docs.views.docs_readme', name='docs_main'),
    (r'^bad/$', bad),
)

urlpatterns += patterns('',
    url(r'', include('mturk.api.urls')),
    url(r'', include('mturk.search.urls')),
    url(r'^classification/', include('mturk.classification.urls')),
    url('', include('mturk.main.urls')),
    url(r'^top_requesters/', include('mturk.toprequesters.urls')),
    url(r'^documentation/', include('sphinxdoc.urls')),
)

#
# POST-INIT
#

## In DEBUG mode, serve media files through Django.
if settings.DEBUG:
    # Remove leading and trailing slashes so the regex matches.
    media_url = settings.MEDIA_URL.lstrip('/').rstrip('/')
    urlpatterns += patterns('',
        (r'^%s/(?P<path>.*)$' % media_url, 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()

if getattr(settings, 'JSCONF_DEVELOPMENT_MODE', False):
    # the urls module always has settings loaded, so execute this command
    # to generate jsconf each time Django starts. This way, we can serve the
    # jsconf.js as a static file.
    # This is enabled only for DEBUG configs, for stable you should run
    #   ./manage.py generatejsconf
    # after every deploy.
    call_command('makejsconf')
