from django.conf.urls import patterns, url, include
from django.contrib import admin
admin.autodiscover()

# Make a regular expression with instruments with available reduction
from reduction_service.settings import REDUCTION_AVAILABLE
valid_instruments = combined = "(" + ")|(".join(REDUCTION_AVAILABLE) + ")"


urlpatterns = patterns('',
    url(r'^$', 'reduction_service.views.home', name='home'),
    url(r'^(?P<instrument_name>%s)/$' % valid_instruments, 'reduction.views.reduction_home', name='reduction_home'),
    
    url(r'^(?P<instrument_name>%s)/experiment/(?P<ipts>[\w\-]+)/$' % valid_instruments, 'reduction.views.experiment', name='reduction_experiment'),
    
    url(r'^(?P<instrument_name>%s)/reduction/$' % valid_instruments, 'reduction.views.reduction_options', name='reduction'),
    url(r'^(?P<instrument_name>%s)/reduction/(?P<reduction_id>\d+)/$' % valid_instruments, 'reduction.views.reduction_options', name='reduction_options'),
    url(r'^(?P<instrument_name>%s)/reduction/(?P<reduction_id>\d+)/download/xml$' % valid_instruments, 'reduction.views.xml_reduction_script', name='reduction_xml_reduction_script'),
    url(r'^(?P<instrument_name>%s)/reduction/(?P<reduction_id>\d+)/download/py$' % valid_instruments, 'reduction.views.py_reduction_script', name='reduction_py_reduction_script'),
    url(r'^(?P<instrument_name>%s)/reduction/(?P<reduction_id>\d+)/submit$' % valid_instruments, 'reduction.views.submit_job', name='reduction_submit_job'),
    url(r'^(?P<instrument_name>%s)/reduction/(?P<reduction_id>\d+)/script$' % valid_instruments, 'reduction.views.reduction_script', name='reduction_script'),
    url(r'^(?P<instrument_name>%s)/reduction/(?P<reduction_id>\d+)/delete$' % valid_instruments, 'reduction.views.delete_reduction', name='reduction_delete'),
    
    url(r'^(?P<instrument_name>%s)/jobs/$' % valid_instruments, 'reduction.views.reduction_jobs', name='reduction_jobs'),
    url(r'^(?P<instrument_name>%s)/query/(?P<job_id>[\w\-\.]+)/$' % valid_instruments, 'reduction.views.job_details', name='reduction_job_details'),
    
    # Those are instrument specific. If the regular expression is met above this is never called!
    url(r'^eqsans/', include('eqsans.urls', namespace='eqsans')),
)
