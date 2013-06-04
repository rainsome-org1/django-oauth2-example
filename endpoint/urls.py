from django.conf.urls import patterns, include, url
from django.contrib import admin

from endpoint.api.ressources import CatResource

cat_resource = CatResource()

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^api/', include(cat_resource.urls)),
    url(r'^core/', include('endpoint.core.urls')),
    url(r'^accounts/', include('endpoint.accounts.urls')),
    url(r'^webprovider/', include('endpoint.web_provider.urls')),
    url(r'^backendprovider/', include('endpoint.backend_provider.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
