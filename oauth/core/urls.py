from django.conf.urls import patterns, url

urlpatterns = patterns('oauth.core.views',
    url(r'^$', 'index', name='core_index'),
)
