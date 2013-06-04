from django.conf.urls import patterns, url

urlpatterns = patterns('endpoint.backend_provider.views',
    url(r'^create_token/$', 'create_token', name='backend_provider_create_token'),
    url(r'^protected_resource/$', 'protected_resource', name='backend_provider_protected_resource'),
    url(r'^error/$', 'error', name='backend_provider_error'),
)
