from django.conf.urls import patterns, include, url

# Namespace seq
urlpatterns = patterns('',
	url(r'^configuration/(?P<config_id>\d+)/submit$' , 'seq.views.configuration_submit', name='configuration_submit'),
)
