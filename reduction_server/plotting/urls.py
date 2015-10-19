from django.conf.urls import patterns, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^adjust1d/(?P<plot_id>\d+)/$', 'reduction_server.plotting.views.adjust_1d', name='plotting_adjust_1d'),
    url(r'^adjust1d/(?P<plot_id>\d+)/update$', 'reduction_server.plotting.views.updated_parameters_1d', name='updated_parameters_1d'),
    url(r'^adjust2d/(?P<plot_id>\d+)/$', 'reduction_server.plotting.views.adjust_2d', name='plotting_adjust_2d'),
    url(r'^adjust2d/(?P<plot_id>\d+)/update$', 'reduction_server.plotting.views.updated_parameters_2d', name='updated_parameters_2d'),
)
