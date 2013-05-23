import datetime
import logging
import sys

from django.contrib.auth import models as auth_models
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from oauth.providers import models as providers_models
from oauthlib.oauth2 import RequestValidator, WebApplicationServer
from oauthlib.oauth2.ext.django import OAuth2ProviderDecorator


log = logging.getLogger('oauthlib')
log.addHandler(logging.StreamHandler(sys.stdout))
log.setLevel(logging.DEBUG)


class SkeletonValidator(RequestValidator):

    # Ordered roughly in order of apperance in the authorization grant flow

    # Pre- and Post-authorization.

    def validate_client_id(self, client_id, request, *args, **kwargs):
        return providers_models.Client.objects.filter(client_id=client_id).exists()

    def validate_redirect_uri(self, client_id, redirect_uri, request, *args, **kwargs):
        # Is the client allowed to use the supplied redirect_uri? i.e. has
        # the client previously registered this EXACT redirect uri.
        return providers_models.Client.objects.filter(
            client_id=client_id,
            redirect_uris__contains=redirect_uri).exists()

    def get_default_redirect_uri(self, client_id, request, *args, **kwargs):
        try:
            client = providers_models.Client.objects.filter(client_id=client_id)
            return client.default_scopes
        except ObjectDoesNotExist:
            return None

    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        # Is the client allowed to access the requested scopes?
        try:
            allowed_scopes = providers_models.Client.objects.get(client_id=client_id).scopes.split()
        except ObjectDoesNotExist:
            return False

        for scope in scopes:
            if scope not in allowed_scopes:
                return False
        return True

    def get_default_scopes(self, client_id, request, *args, **kwargs):
        # Scopes a client will authorize for if none are supplied in the
        # authorization request.
        try:
            return providers_models.Client.objects.get(client_id=client_id).default_scopes.split()
        except ObjectDoesNotExist:
            return None

    def validate_response_type(self, client_id, response_type, client, request, *args, **kwargs):
        # Clients should only be allowed to use one type of response type, the
        # one associated with their one allowed grant type.
        # In this case it must be "code".
        # FIXME See comment in my tests
        return True

    # Post-authorization

    def save_authorization_code(self, client_id, code, request, *args, **kwargs):
        # Remember to associate it with request.scopes, request.redirect_uri
        # request.client, request.state and request.user (the last is passed in
        # post_authorization credentials, i.e. { 'user': request.user}.
        # Warning client_id is not client.pk!
        client = providers_models.Client.objects.get(client_id=client_id)
        user = auth_models.User.objects.get(pk=request.user.pk)
        providers_models.AuthorizationCode.objects.create(
            client=client,
            user=user,
            # FIXME Extracted from dict!
            code=code['code'],
            scopes=" ".join(request.scopes),
            expires_at=timezone.now(),
            # FIXME Not in original model
            redirect_uri=request.redirect_uri,
            # FIXME No state in models!
        )
        return True

    # Token request

    def authenticate_client(self, request, *args, **kwargs):
        # Whichever authentication method suits you, HTTP Basic might work
        request.client = providers_models.Client.objects.get(client_id=request.client_id)
        return True

    def authenticate_client_id(self, client_id, request, *args, **kwargs):
        # Don't allow public (non-authenticated) clients
        return False

    def validate_code(self, client_id, code, client, request, *args, **kwargs):
        # Validate the code belongs to the client. Add associated scopes,
        # state and user to request.scopes, request.state and request.user.
        # FIXME No state to save
        if client_id != client.client_id:
            return False

        try:
            authorization_code = providers_models.AuthorizationCode.objects.get(client=client, code=code)
        except ObjectDoesNotExist:
            return False

        request.scopes = authorization_code.scopes.split()
        print request.scopes
        request.user = client.user
        return True

    def confirm_redirect_uri(self, client_id, code, redirect_uri, client, *args, **kwargs):
        # You did save the redirect uri with the authorization code right?
        try:
            authorization_code = providers_models.AuthorizationCode.objects.get(client=client, code=code)
        except ObjectDoesNotExist:
            return False

        return redirect_uri == authorization_code.redirect_uri

    def validate_grant_type(self, client_id, grant_type, client, request, *args, **kwargs):
        # Clients should only be allowed to use one type of grant.
        # In this case, it must be "authorization_code" or "refresh_token"
        return grant_type in ("authorization_code", "refresh_token")

    def save_bearer_token(self, token, request, *args, **kwargs):
        # Remeber to associate it with request.scopes, request.user and
        # request.client. The two former will be set when you validate
        # the authorization code. Don't forget to save both the
        # access_token and the refresh_token and set expiration for the
        # access_token to now + expires_in seconds.
        providers_models.Token.objects.create(
            client=request.client,
            user=request.user,
            scopes=request.scopes,
            access_token=token['access_token'],
            refresh_token=token['refresh_token'],
            expires_at=timezone.now() + datetime.timedelta(seconds=token['expires_in']),
        )

    def invalidate_authorization_code(self, client_id, code, request, *args, **kwargs):
        # Authorization codes are use once, invalidate it when a Bearer token
        # has been acquired.
        try:
            providers_models.AuthorizationCode.objects.get(client=request.client, code=code).delete()
        except ObjectDoesNotExist:
            pass
        return True

    # Protected resource request

    def validate_bearer_token(self, token, scopes, request):
        # Remember to check expiration and scope membership
        import ipdb; ipdb.set_trace()
        pass

    # Token refresh request

    def confirm_scopes(self, refresh_token, scopes, request, *args, **kwargs):
        # If the client requests a set of scopes, assure that those are the
        # same as, or a subset of, the ones associated with the token earlier.
        import ipdb; ipdb.set_trace()
        pass


validator = SkeletonValidator()
server = WebApplicationServer(validator)
provider = OAuth2ProviderDecorator('/error', server)    # See next section


@login_required
@provider.pre_authorization_view
def authorize(request, client_id=None, scopes=None, state=None, redirect_uri=None, response_type=None):
    # This is the traditional authorization page
    # Scopes will be the list of scopes client requested access too
    # You will want to present them in a nice form where the user can
    # select which scopes they allow the client to access.
    response = HttpResponse()
    response.write('<h1>Authorize access to %s</h1>' % client_id)
    response.write('<form method="POST" action="%s">' % reverse('providers_authorization'))
    scopes = ['ham', 'jam']
    for scope in scopes or []:
        response.write('<input type="checkbox" name="scopes" value="%s"/> %s' % (scope, scope))
    response.write('<input type="submit" value="Authorize"/>')
    return response

# @csrf_exempt
@login_required
@provider.post_authorization_view
def authorization_response(request):
    # This is where the form submitted from authorize should end up
    # Which scopes user authorized access to + extra credentials you want
    # appended to the request object passed into the validator methods.
    # In almost every case, you will want to include the current
    # user in these extra credentials in order to associate the user with
    # the authorization code or bearer token.
    return request.POST.getlist('scopes'), {'user': request.user}


@provider.access_token_view
def token_response(request):
    # Not much too do here for you, return a dict with extra credentials
    # you want appended to request.credentials passed to the save_bearer_token
    # method of the validator.
    return {'extra': 'creds'}


def error(request):
    # The /error page users will be redirected to if there was something
    # wrong with the credentials the client included when redirecting the
    # user to the authorization form. Mainly if the client was invalid or
    # included a malformed / invalid redirect url.
    # Error and description can be found in
    # GET['error'] and GET['error_description']
    return HttpResponse('Bad client! Warn user!')


# FIXME Not used
@provider.protected_resource_view(scopes=['images'])
def i_am_protected(request, client, resource_owner, **kwargs):
    # One of your many OAuth 2 protected resource views
    # Returns whatever you fancy
    # May be bound to various scopes of your choosing
    return HttpResponse('pictures of cats')
