from django.conf.urls import url
from . import views
# Namespace seq
urlpatterns = [
	url(r'^configuration/(?P<config_id>\d+)/submit$' , views.configuration_submit, name='configuration_submit'),
]
