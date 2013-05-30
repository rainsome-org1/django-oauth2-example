from django.conf.urls import patterns, url

urlpatterns = patterns('oauth.web_provider.views',
    url(r'^authorize/$', 'authorize', name='web_provider_authorize'),
    url(r'^post_authorization/$', 'authorization_response', name='web_provider_authorization'),
    url(r'^create_token/$', 'token_response', name='web_provider_create_token'),
    url(r'^protected_resource/$', 'protected_resource', name='web_provider_protected_resource'),
)
