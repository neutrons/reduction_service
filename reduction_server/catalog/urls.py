from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.instrument_list, name='catalog'),
    url(r'^(?P<instrument>[\w]+)/$', views.experiment_list, name='catalog_experiments'),
    url(r'^(?P<instrument>[\w]+)/(?P<ipts>[\w\-\.]+)/$', views.experiment_run_list, name='catalog_runs'),
    url(r'^(?P<instrument>[\w]+)/(?P<ipts>[\w\-\.]+)/autoreduced$', views.download_autoreduced, name='catalog_get_autoreduced'),
    url(r'^(?P<instrument>[\w]+)/run/(?P<run_number>\d+)/', views.run_info, name='catalog_run_info'),
    url(r'^download/(?P<job_id>\d+)/(?P<filename>[\w\-\.]+)$', views.download_link, name='catalog_download_link'),
    #url(r'^(?P<instrument>[\w]+)/(?P<ipts>[\w\-\.]+)/jsonruns$', views.run_range', name='catalog_json_runs'),
    url(r'^(?P<instrument>[\w]+)/(?P<ipts>[\w\-\.]+)/runsjson$', views.runs_json, name='catalog_runs_json'),
    url(r'^(?P<instrument>[\w]+)/experimentsjson$', views.experiments_json, name='catalog_experiments_json'),
]
