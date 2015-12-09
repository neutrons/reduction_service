from django.conf.urls import url
from . import views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    url(r'^adjust1d/(?P<plot_id>\d+)/$', views.adjust_1d, name='plotting_adjust_1d'),
    url(r'^adjust1d/(?P<plot_id>\d+)/update$', views.updated_parameters_1d, name='updated_parameters_1d'),
    url(r'^adjust2d/(?P<plot_id>\d+)/$', views.adjust_2d, name='plotting_adjust_2d'),
    url(r'^adjust2d/(?P<plot_id>\d+)/update$', views.updated_parameters_2d, name='updated_parameters_2d'),
]
