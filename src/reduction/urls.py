from django.conf.urls import patterns, url, include
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'reduction_service.views.home', name='home'),
    url(r'^(?P<instrument_name>\w+)/$', 'reduction.views.reduction_home', name='reduction_home'),
    
    url(r'^(?P<instrument_name>\w+)/experiment/(?P<ipts>[\w\-]+)/$', 'reduction.views.experiment', name='reduction_experiment'),
    
    url(r'^(?P<instrument_name>\w+)/reduction/$', 'reduction.views.reduction_options', name='reduction_options'),
    url(r'^(?P<instrument_name>\w+)/reduction/(?P<reduction_id>\d+)/$', 'reduction.views.reduction_options', name='reduction'),
    url(r'^(?P<instrument_name>\w+)/reduction/(?P<reduction_id>\d+)/download/xml$', 'reduction.views.xml_reduction_script', name='reduction_xml_reduction_script'),
    url(r'^(?P<instrument_name>\w+)/reduction/(?P<reduction_id>\d+)/download/py$', 'reduction.views.py_reduction_script', name='reduction_py_reduction_script'),
    url(r'^(?P<instrument_name>\w+)/reduction/(?P<reduction_id>\d+)/submit$', 'reduction.views.submit_job', name='reduction_submit_job'),
    url(r'^(?P<instrument_name>\w+)/reduction/(?P<reduction_id>\d+)/script$', 'reduction.views.reduction_script', name='reduction_script'),
    url(r'^(?P<instrument_name>\w+)/reduction/(?P<reduction_id>\d+)/delete$', 'reduction.views.delete_reduction', name='reduction_delete'),
    
    url(r'^(?P<instrument_name>\w+)/configuration/$', 'reduction.views.reduction_configuration', name='reduction_new_configuration'),
    url(r'^(?P<instrument_name>\w+)/configuration/(?P<config_id>\d+)/$', 'reduction.views.reduction_configuration', name='reduction_configuration'),
    url(r'^(?P<instrument_name>\w+)/configuration/(?P<config_id>\d+)/delete$', 'reduction.views.configuration_delete', name='configuration_delete'),
    url(r'^(?P<instrument_name>\w+)/configuration/(?P<config_id>\d+)/submit$', 'reduction.views.configuration_submit', name='configuration_submit'),
    url(r'^(?P<instrument_name>\w+)/configuration/(?P<config_id>\d+)/(?P<reduction_id>\d+)/delete$', 'reduction.views.configuration_job_delete', name='configuration_job_delete'),
    
    url(r'^(?P<instrument_name>\w+)/jobs/$', 'reduction.views.reduction_jobs', name='reduction_jobs'),
    
    # Those are just forwards: General templates need these!!!
    url(r'^(?P<instrument_name>\w+)/query/(?P<job_id>[\w\-\.]+)/$', 'reduction.views.job_details', name='reduction_job_details'),
    url(r'^(?P<instrument_name>\w+)/configuration/query/(?P<remote_set_id>\d+)/$', 'reduction.views.configuration_query', name='configuration_query'),
    url(r'^(?P<instrument_name>\w+)/configuration/iq/(?P<remote_set_id>\d+)/$', 'reduction.views.configuration_iq', name='configuration_iq'),
    
    # Those are instrument specific. If the regular expression is met above this is never called!
    #url(r'^eqsans/', include('reduction.eqsans.urls')),
    url(r'^eqsans/', include('eqsans.urls') ),
)
