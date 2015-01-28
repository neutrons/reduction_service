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
    url(r'^(?P<instrument_name>\w+)/configuration/$', 'reduction.views.reduction_configuration', name='reduction_new_configuration'),
    url(r'^(?P<instrument_name>\w+)/configuration/(?P<config_id>\d+)/$', 'reduction.views.reduction_configuration', name='reduction_configuration'),
    url(r'^(?P<instrument_name>\w+)/configuration/(?P<config_id>\d+)/delete$',
        'reduction.views.reduction_configuration_delete', name='reduction_configuration_delete'),
    url(r'^(?P<instrument_name>\w+)/configuration/(?P<config_id>\d+)/(?P<reduction_id>\d+)/delete$',
        'reduction.views.reduction_configuration_job_delete', name='reduction_configuration_job_delete'),
    url(r'^(?P<instrument_name>\w+)/configuration/(?P<config_id>\d+)/submit$', 'reduction.views.reduction_configuration_submit', name='reduction_configuration_submit'),
    url(r'^(?P<instrument_name>\w+)/reduction/(?P<reduction_id>\d+)/download/xml$', 'reduction.views.xml_reduction_script', name='reduction_xml_reduction_script'),
    url(r'^(?P<instrument_name>\w+)/reduction/(?P<reduction_id>\d+)/download/py$', 'reduction.views.py_reduction_script', name='reduction_py_reduction_script'),
    url(r'^(?P<instrument_name>\w+)/reduction/(?P<reduction_id>\d+)/submit$', 'reduction.views.submit_job', name='reduction_submit_job'),
    url(r'^(?P<instrument_name>\w+)/reduction/(?P<reduction_id>\d+)/script$', 'reduction.views.reduction_script', name='reduction_reduction_script'),
    
    # Those are just forwards: General templates need these!!!
    url(r'^(?P<instrument_name>\w+)/query/(?P<job_id>[\w\-\.]+)/$', 'reduction.views.job_details', name='reduction_job_details'),
    url(r'^(?P<instrument_name>\w+)/configuration/query/(?P<remote_set_id>\d+)/$', 'reduction.views.reduction_configuration_query', name='reduction_configuration_query'),
    url(r'^(?P<instrument_name>\w+)/configuration/iq/(?P<remote_set_id>\d+)/$', 'reduction.views.reduction_configuration_iq', name='reduction_configuration_iq'),
)
