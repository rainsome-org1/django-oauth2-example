import logging
import sys
import datetime

from oauthlib.oauth2 import RequestValidator, BackendApplicationServer
from oauthlib.oauth2.ext.django import OAuth2ProviderDecorator

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils import timezone

from oauth.backend_provider.models import ApplicationClient, ApplicationToken

log = logging.getLogger('oauthlib')
log.addHandler(logging.StreamHandler(sys.stdout))
log.setLevel(logging.DEBUG)


class BackendValidator(RequestValidator):
    # Token request

    # FIXME No password in backtrace...
    def authenticate_client(self, request, *args, **kwargs):
        client_token = request.headers.get('HTTP_CLIENT')
        if not ':' in client_token:
            return False

        client_id, client_secret = client_token.split(':')
        if not client_secret:
            return False

        try:
            request.client = ApplicationClient.objects.get(client_id=client_id)
        except ApplicationClient.DoesNotExist:
            return False

        # Authenticate client
        params = dict(request.uri_query_params)
        username = params.get('username')
        password = params.get('password')
        if not username or not password:
            return False

        UserModel = get_user_model()
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
            if user.check_password(password):
                request.user = user
                return True
        except UserModel.DoesNotExist:
            return False

    def validate_grant_type(self, client_id, grant_type, client, request, *args, **kwargs):
        return grant_type == "client_credentials"

    def get_default_scopes(self, client_id, request, *args, **kwargs):
        # Scopes a client will authorize for if none are supplied in the
        # authorization request.
        try:
            return ApplicationClient.objects.get(client_id=client_id).default_scopes.split()
        except ApplicationClient.DoesNotExist:
            return None

    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        # Is the client allowed to access the requested scopes?
        try:
            allowed_scopes = ApplicationClient.objects.get(client_id=client_id).allowed_scopes.split()
        except ApplicationClient.DoesNotExist:
            return False

        for scope in scopes:
            if scope not in allowed_scopes:
                return False
        return True

    def save_bearer_token(self, token, request, *args, **kwargs):
        ApplicationToken.objects.create(
            application=request.client,
            user=request.user,
            scopes=" ".join(request.scopes),
            access_token=token['access_token'],
            expires_at=timezone.now() + datetime.timedelta(seconds=token['expires_in']),
        )

    # Protected resource request

    def validate_bearer_token(self, token, scopes, request):
        # Remember to check expiration and scope membership
        # FIXME Not sure about scopes meaning
        try:
            app_token = ApplicationToken.objects.get(
                access_token=token,
                expires_at__gte=timezone.now()
            )
            app_token_scopes = set(app_token.scopes.split())
            scopes = set(scopes)
            if scopes.intersection(app_token_scopes):
                return True
        except ApplicationToken.DoesNotExist:
            pass

        return False


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
