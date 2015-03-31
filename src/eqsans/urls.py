from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^squery/dummy$', 'eqsans.views.test_result'),
    
    url(r'^configuration/$' , 'eqsans.views.configuration_options', name='configuration'),
    url(r'^configuration/(?P<config_id>\d+)/$' , 'eqsans.views.configuration_options', name='configuration_options'),
    url(r'^configuration/(?P<config_id>\d+)/delete$' , 'eqsans.views.configuration_delete', name='configuration_delete'),
    url(r'^configuration/(?P<config_id>\d+)/submit$' , 'eqsans.views.configuration_submit', name='configuration_submit'),
    url(r'^configuration/(?P<config_id>\d+)/(?P<reduction_id>\d+)/delete$', 'eqsans.views.configuration_job_delete', name='configuration_job_delete'),
    url(r'^configuration/iq/(?P<remote_set_id>\d+)/$', 'eqsans.views.configuration_iq', name='configuration_iq'),
    url(r'^configuration/query/(?P<remote_set_id>\d+)/$', 'eqsans.views.configuration_query', name='configuration_query'),
    
)
