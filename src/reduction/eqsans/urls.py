from django.conf.urls import patterns, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^query/(?P<job_id>[\w\-\.]+)/$', 'eqsans.views.job_details', name='eqsans_job_details'),
    url(r'^configuration/query/(?P<remote_set_id>\d+)/$', 'eqsans.views.reduction_configuration_query', name='eqsans_configuration_query'),
    url(r'^configuration/iq/(?P<remote_set_id>\d+)/$', 'eqsans.views.reduction_configuration_iq', name='eqsans_configuration_iq'),
    url(r'^query/dummy$', 'eqsans.views.test_result'),
)
