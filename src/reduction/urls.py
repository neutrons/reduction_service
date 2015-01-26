from django.conf.urls import patterns, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^(?P<instrument_name>\w+)/$', 'reduction.views.reduction_home', name='reduction_reduction_home'),

)
