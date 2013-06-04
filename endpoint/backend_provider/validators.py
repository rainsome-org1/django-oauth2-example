import datetime

from oauthlib.oauth2 import RequestValidator

from django.contrib.auth import get_user_model
from django.utils import timezone

from endpoint.backend_provider.models import ApplicationClient, ApplicationToken


class BackendValidator(RequestValidator):
    # Token request

    # FIXME No password in backtrace...
    # FIXME POST instead of GET
    # FIXME Only one access token at once by client/user pair
    def authenticate_client(self, request, *args, **kwargs):
        client_token = request.headers.get('HTTP_CLIENT')
        if not client_token or not ':' in client_token:
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
                request.client = app_token.application
                request.user = app_token.user
                return True

        except ApplicationToken.DoesNotExist:
            pass

        return False
