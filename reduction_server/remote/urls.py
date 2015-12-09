from django.conf.urls import url
from django.contrib import admin
admin.autodiscover()

from . import views

urlpatterns = [
    url(r'^jobs/$', views.query_remote_jobs, name='remote_query_jobs'),
    url(r'^authenticate/$', views.authenticate, name='remote_authenticate'),
    url(r'^query/(?P<job_id>[\w\-\.]+)/$', views.job_details, name='remote_job_details'),
    url(r'^download/(?P<trans_id>\d+)/(?P<filename>[\w\-\.]+)$', views.download_file, name='remote_download'),
    url(r'^download/(?P<trans_id>\d+)/(?P<filename>[\w\-\.]+)/delete$', views.download_file_and_delete, name='remote_download_and_delete'),
    url(r'^transaction/(?P<trans_id>\d+)/stop/$', views.stop_transaction, name='remote_stop_transaction'),
]
