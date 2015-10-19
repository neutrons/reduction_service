from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^squery/dummy$', 'eqsans.views.test_result'),
    
)
