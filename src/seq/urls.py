from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
	url(r'^configuration/(?P<config_id>\d+)/submit$' , 'seq.views.configuration_submit', name='seq:configuration_submit'),
)
