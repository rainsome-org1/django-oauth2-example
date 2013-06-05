import datetime

from oauthlib.oauth2 import RequestValidator

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables, sensitive_post_parameters

from endpoint.backend_provider.models import ApplicationClient, ApplicationToken


class BackendValidator(RequestValidator):
    # Token request

    @sensitive_variables('username', 'password')
    @sensitive_post_parameters('username', 'password')
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
        if request.http_method == 'POST':
            params = dict(request.decoded_body)
        else:
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
        # Only one token by client/user
        ApplicationToken.objects.filter(
            application=request.client,
            user=request.user).delete()

        ApplicationToken.objects.create(
            application=request.client,
            user=request.user,
            scopes=" ".join(request.scopes),
            access_token=token['access_token'],
            expires_at=timezone.now() + datetime.timedelta(seconds=token['expires_in']),
        )

    # Protected resource request

    def validate_bearer_token(self, token, scopes, request):
        # Scopes of application token are the allowed scopes and  all requested
        # scopes must be present in application token scopes.
        try:
            app_token = ApplicationToken.objects.get(
                access_token=token,
                expires_at__gte=timezone.now()
            )

            app_token_scopes = app_token.scopes.split()
            for scope in scopes:
                if scope not in app_token_scopes:
                    return False

        except ApplicationToken.DoesNotExist:
            return False

        request.client = app_token.application
        request.user = app_token.user
        return True
