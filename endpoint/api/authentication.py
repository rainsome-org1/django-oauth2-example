# -*- coding: utf-8 -*-
# Copyright (c) 2013 Polyconseil SAS. All rights reserved.

from oauthlib.common import urlencode
from oauthlib.oauth2 import BackendApplicationServer
from oauthlib.oauth2.ext.django import OAuth2ProviderDecorator

from tastypie import exceptions, http
from tastypie.authentication import Authentication

from django.utils.translation import ugettext_lazy as _

from endpoint.backend_provider.validators import BackendValidator


class Unauthorized(exceptions.ImmediateHttpResponse):
    """A helper to raise an unauthorized exception."""
    def __init__(self):
        self.response = http.HttpUnauthorized(_(u"You are not authorized."))


class BackendAuthentication(Authentication):
    """OAauth2 Backend Authentication"""

    def __init__(self, **kwargs):
        super(BackendAuthentication, self).__init__(**kwargs)
        self.validator = BackendValidator()
        self.server = BackendApplicationServer(self.validator)
        self.provider = OAuth2ProviderDecorator('/error', self.server)
        # FIXME
        self.scopes = ['ham', 'jam']

    def _unauthorized(self):
        return http.HttpUnauthorized()

    def _extract_params(self, request):
        uri = request.build_absolute_uri()
        http_method = request.method
        headers = request.META

        if 'wsgi.input' in headers:
            del headers['wsgi.input']

        if 'wsgi.errors' in headers:
            del headers['wsgi.errors']

        if 'HTTP_AUTHORIZATION' in headers:
            headers['Authorization'] = headers['HTTP_AUTHORIZATION']

        body = urlencode(request.POST.items())
        return uri, http_method, body, headers

    def is_authenticated(self, request, **kwargs):
        uri, http_method, body, headers = self._extract_params(request)
        valid, r = self.provider._resource_endpoint.verify_request(
            uri, http_method, body, headers, self.scopes)
        request.client = r.client
        request.user = r.user
        request.scopes = self.scopes
        return valid

    def get_identifier(self, request):
        return request.user.username
