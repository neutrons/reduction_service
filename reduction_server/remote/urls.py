from django.conf.urls import patterns, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^jobs/$', 'reduction_server.remote.views.query_remote_jobs', name='remote_query_jobs'),
    url(r'^authenticate/$', 'reduction_server.remote.views.authenticate', name='remote_authenticate'),
    url(r'^query/(?P<job_id>[\w\-\.]+)/$', 'reduction_server.remote.views.job_details', name='remote_job_details'),
    url(r'^download/(?P<trans_id>\d+)/(?P<filename>[\w\-\.]+)$', 'reduction_server.remote.views.download_file', name='remote_download'),
    url(r'^download/(?P<trans_id>\d+)/(?P<filename>[\w\-\.]+)/delete$', 'reduction_server.remote.views.download_file_and_delete', name='remote_download_and_delete'),
    url(r'^transaction/(?P<trans_id>\d+)/stop/$', 'reduction_server.remote.views.stop_transaction', name='remote_stop_transaction'),
)
