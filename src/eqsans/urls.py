from django.conf.urls import patterns, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    #url(r'^$', 'eqsans.views.reduction_home', name='eqsans_reduction_home'),
    url(r'^experiment/(?P<ipts>[\w\-]+)/$', 'eqsans.views.experiment', name='eqsans_experiment'),
    url(r'^reduction/$', 'eqsans.views.reduction_options', name='eqsans_new_reduction'),
    url(r'^reduction/(?P<reduction_id>\d+)/$', 'eqsans.views.reduction_options', name='eqsans_reduction'),
    url(r'^reduction/(?P<reduction_id>\d+)/script$', 'eqsans.views.reduction_script', name='eqsans_reduction_script'),
    url(r'^reduction/(?P<reduction_id>\d+)/submit$', 'eqsans.views.submit_job', name='eqsans_submit_job'),
    url(r'^reduction/(?P<reduction_id>\d+)/delete$', 'eqsans.views.delete_reduction', name='eqsans_delete_reduction'),
    url(r'^reduction/(?P<reduction_id>\d+)/download/py$', 'eqsans.views.py_reduction_script', name='eqsans_py_reduction_script'),
    url(r'^reduction/(?P<reduction_id>\d+)/download/xml$', 'eqsans.views.xml_reduction_script', name='eqsans_xml_reduction_script'),
    url(r'^query/(?P<job_id>[\w\-\.]+)/$', 'eqsans.views.job_details', name='eqsans_job_details'),
    url(r'^query/dummy$', 'eqsans.views.test_result'),
    url(r'^jobs/$', 'eqsans.views.reduction_jobs', name='eqsans_reduction_jobs'),
    url(r'^configuration/$', 'eqsans.views.reduction_configuration', name='eqsans_new_configuration'),
    url(r'^configuration/(?P<config_id>\d+)/$', 'eqsans.views.reduction_configuration', name='eqsans_configuration'),
    url(r'^configuration/(?P<config_id>\d+)/delete$', 'eqsans.views.reduction_configuration_delete', name='eqsans_configuration_delete'),
    url(r'^configuration/(?P<config_id>\d+)/submit$', 'eqsans.views.reduction_configuration_submit', name='eqsans_configuration_submit'),
    url(r'^configuration/query/(?P<remote_set_id>\d+)/$', 'eqsans.views.reduction_configuration_query', name='eqsans_configuration_query'),
    url(r'^configuration/iq/(?P<remote_set_id>\d+)/$', 'eqsans.views.reduction_configuration_iq', name='eqsans_configuration_iq'),
    url(r'^configuration/(?P<config_id>\d+)/(?P<reduction_id>\d+)/delete$', 'eqsans.views.reduction_configuration_job_delete', name='eqsans_configuration_job_delete'),

)
