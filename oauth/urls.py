from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^core/', include('oauth.core.urls')),
    url(r'^accounts/', include('oauth.accounts.urls')),
    url(r'^webprovider/', include('oauth.web_provider.urls')),
    url(r'^backendprovider/', include('oauth.backend_provider.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
