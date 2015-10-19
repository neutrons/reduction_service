from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^login$', 'reduction_server.users.views.perform_login'),
    url(r'^logout$', 'reduction_server.users.views.perform_logout'),
)
