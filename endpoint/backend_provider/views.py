import logging
import sys

from oauthlib.oauth2 import BackendApplicationServer
from oauthlib.oauth2.ext.django import OAuth2ProviderDecorator

from django.http import HttpResponse

from endpoint.backend_provider.validators import BackendValidator

log = logging.getLogger('endpoint')
log.addHandler(logging.StreamHandler(sys.stdout))
log.setLevel(logging.DEBUG)


validator = BackendValidator()
server = BackendApplicationServer(validator)
provider = OAuth2ProviderDecorator('/backendprovider/error', server)    # See next section


@provider.access_token_view
def create_token(request):
    # Not much too do here for you, return a dict with extra credentials
    # you want appended to request.credentials passed to the save_bearer_token
    # method of the validator.
    return {}


@provider.protected_resource_view(scopes=['ham'])
def protected_resource(request, client=None, user=None, scopes=None):
    # One of your many OAuth 2 protected resource views
    # Returns whatever you fancy
    # May be bound to various scopes of your choosing
    return HttpResponse('Pictures of cats')


def error(request):
    return HttpResponse('fail')
