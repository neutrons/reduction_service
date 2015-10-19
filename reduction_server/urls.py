from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'reduction_server.views.home', name='home'),
    url(r'^reduction/', include('reduction_server.reduction.urls')), # general reductions
    url(r'^remote/', include('reduction_server.remote.urls')),
    url(r'^catalog/', include('reduction_server.catalog.urls')),
    url(r'^plotting/', include('reduction_server.plotting.urls')),
    url(r'^users/', include('reduction_server.users.urls')),
    url(r'^database/doc/', include('django.contrib.admindocs.urls')),
    url(r'^database/', include(admin.site.urls)),
    url(r'^seq/', include('reduction_server.seq.urls',  namespace="seq")), # specific views for SEQ
)

# if settings.DEBUG_TOOLBAR:
#     import debug_toolbar
#     urlpatterns += patterns('',
#         url(r'^__debug__/', include(debug_toolbar.urls)),
#     )