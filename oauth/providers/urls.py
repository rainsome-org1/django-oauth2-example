from django.conf.urls import patterns, url

urlpatterns = patterns('oauth.providers.views',
    url(r'^authorize/$', 'authorize', name='providers_authorize'),
    url(r'^post_authorization/$', 'authorization_response', name='providers_authorization'),
    url(r'^create_token/$', 'token_response', name='providers_create_token'),
)
