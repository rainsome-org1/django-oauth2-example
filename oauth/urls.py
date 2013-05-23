from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^core/', include('oauth.core.urls')),
    url(r'^accounts/', include('oauth.accounts.urls')),
    url(r'^oauth/', include('oauth.providers.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
