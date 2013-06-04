from django.conf.urls import patterns, url

urlpatterns = patterns('endpoint.core.views',
    url(r'^$', 'index', name='core_index'),
)
