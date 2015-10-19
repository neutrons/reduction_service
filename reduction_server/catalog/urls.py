from django.conf.urls import patterns, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'reduction_server.catalog.views.instrument_list', name='catalog'),
    url(r'^(?P<instrument>[\w]+)/$', 'reduction_server.catalog.views.experiment_list', name='catalog_experiments'),
    url(r'^(?P<instrument>[\w]+)/(?P<ipts>[\w\-\.]+)/$', 'reduction_server.catalog.views.experiment_run_list', name='catalog_runs'),
    url(r'^(?P<instrument>[\w]+)/(?P<ipts>[\w\-\.]+)/autoreduced$', 'reduction_server.catalog.views.download_autoreduced', name='catalog_get_autoreduced'),
    url(r'^(?P<instrument>[\w]+)/run/(?P<run_number>\d+)/', 'reduction_server.catalog.views.run_info', name='catalog_run_info'),
    url(r'^download/(?P<job_id>\d+)/(?P<filename>[\w\-\.]+)$', 'reduction_server.catalog.views.download_link', name='catalog_download_link'),
    #url(r'^(?P<instrument>[\w]+)/(?P<ipts>[\w\-\.]+)/jsonruns$', 'reduction_server.catalog.views.run_range', name='catalog_json_runs'),
    url(r'^(?P<instrument>[\w]+)/(?P<ipts>[\w\-\.]+)/runsjson$', 'reduction_server.catalog.views.runs_json', name='catalog_runs_json'),
    url(r'^(?P<instrument>[\w]+)/experimentsjson$', 'reduction_server.catalog.views.experiments_json', name='catalog_experiments_json'),
)
