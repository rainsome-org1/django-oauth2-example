# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import requests

from django.contrib.auth import models as auth_models
from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2

from endpoint.backend_provider import models as backend_models


class BackendProviderTest(LiveServerTestCase):

    def setUp(self):
        self.live_url = 'https://localhost:8443'

        self.client_id = 'raymond'
        self.secret = '1234'
        self.scopes = ['ham']
        self.application = backend_models.ApplicationClient.objects.create(
            client_id=self.client_id,
            secret=self.secret,
            allowed_scopes=" ".join(self.scopes),
            default_scopes=" ".join(self.scopes))

        self.user = auth_models.User.objects.create(
            username='johndoe',
            email='johndoe@example.com')
        self.password = 'password'
        self.user.set_password(self.password)
        self.user.save()

    def test_client_credentials(self):
        backend = BackendApplicationClient(self.client_id)
        # Access ressource with new access_token
        url = self.live_url + reverse('backend_provider_create_token')

        headers = {
            'client': '%s:%s' % (self.application.client_id, self.application.secret)
        }

        # Test GET
        credentials = {
            'password': self.password,
            'username': self.user.username,
            'grant_type': 'client_credentials',
        }
        r = requests.get(url, headers=headers, params=credentials, verify=False)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(backend_models.ApplicationToken.objects.count(), 1)

        # Test POST
        r = requests.post(url, credentials, headers=headers, verify=False)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(backend_models.ApplicationToken.objects.count(), 1)

        token = json.loads(r.content)

        # Check only one token in DB

        oauth2 = OAuth2(client=backend, token=token)
        url = self.live_url + reverse('backend_provider_protected_resource')
        r = requests.get(url, auth=oauth2, verify=False)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, "Pictures of cats")
