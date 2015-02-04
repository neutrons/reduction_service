from django.conf.urls import patterns, url
from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns('',
    url(r'^squery/(?P<job_id>[\w\-\.]+)/$', 'eqsans.views.job_details', name='eqsans_job_details'),
    url(r'^sconfiguration/query/(?P<remote_set_id>\d+)/$', 'eqsans.views.reduction_configuration_query', name='eqsans_configuration_query'),
    url(r'^sconfiguration/iq/(?P<remote_set_id>\d+)/$', 'eqsans.views.reduction_configuration_iq', name='eqsans_configuration_iq'),
    url(r'^squery/dummy$', 'eqsans.views.test_result'),
)
