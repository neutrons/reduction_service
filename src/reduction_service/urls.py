from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'reduction_service.views.home', name='home'),
    url(r'^reduction/', include('reduction.urls')), # general reductions
    url(r'^remote/', include('remote.urls')),
    url(r'^catalog/', include('catalog.urls')),
    url(r'^plotting/', include('plotting.urls')),
    url(r'^users/', include('users.urls')),
    url(r'^database/doc/', include('django.contrib.admindocs.urls')),
    url(r'^database/', include(admin.site.urls)),
    url(r'^seq/', include('seq.urls',  namespace="seq")), # specific views for SEQ
)

if settings.DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )