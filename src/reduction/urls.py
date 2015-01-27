from django.conf.urls import patterns, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^(?P<instrument_name>\w+)/$', 'reduction.views.reduction_home', name='reduction_reduction_home'),
    url(r'^(?P<instrument_name>\w+)/experiment/(?P<ipts>[\w\-]+)/$', 'reduction.views.experiment', name='reduction_experiment'),
    url(r'^(?P<instrument_name>\w+)/reduction/(?P<reduction_id>\d+)/delete$', 'reduction.views.delete_reduction', name='reduction_delete_reduction'),
    url(r'^(?P<instrument_name>\w+)/reduction/$', 'reduction.views.reduction_options', name='reduction_new_reduction'),
    url(r'^(?P<instrument_name>\w+)/reduction/(?P<reduction_id>\d+)/$', 'reduction.views.reduction_options', name='reduction_reduction'),
    url(r'^(?P<instrument_name>\w+)/jobs/$', 'reduction.views.reduction_jobs', name='reduction_reduction_jobs'),
    url(r'^(?P<instrument_name>\w+)/configuration/$', 'reduction.views.reduction_configuration', name='eqsans_new_configuration'),
    url(r'^(?P<instrument_name>\w+)/configuration/(?P<config_id>\d+)/$', 'reduction.views.reduction_configuration', name='eqsans_configuration'),

)
