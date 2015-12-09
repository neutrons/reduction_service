from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^squery/dummy$', views.test_result),
    
)
