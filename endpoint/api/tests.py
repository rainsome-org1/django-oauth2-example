# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from django.contrib.auth import models as auth_models
from django.core.urlresolvers import reverse
from django.test import TestCase

from endpoint.backend_provider import models as backend_models
from endpoint.core import models as core_models


class ApiAuthenticationTest(TestCase):
    # Create token via GET
    # curl -i -H "Client: raymond:1234" 'http://127.0.0.1:8000/backendprovider/create_token/
    # ?grant_type=client_credentials&username=johndoe&password=password'
    #
    # Create token via POST
    # curl -i -H "Client: raymond:1234" -X POST
    # --data '{"grant_type": "client_credentials", "username": "johndoe", "password": "password"}'
    # http://127.0.0.1:8000/backendprovider/create_token/

    # Replace XXXX with received access_token
    # curl -i -H "Accept: application/json" -H "Authorization: Bearer XXXX"
    # http://127.0.0.1:8000/api/cat/

    def setUp(self):
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

        self.cat = core_models.Cat.objects.create(name='Kitty')

    def test_client_credentials(self):
        # Access ressource with new access_token
        url = reverse('backend_provider_create_token')

        headers = {
            'HTTP_ACCEPT': 'application/json',
            'HTTP_CLIENT': '%s:%s' % (self.application.client_id, self.application.secret),
        }
        params = {
            'grant_type': 'client_credentials',
            'username': self.user.username,
            'password': self.password
        }
        r = self.client.get(url, params, **headers)
        self.assertEqual(r.status_code, 200)

        token = json.loads(r.content)
        headers = {
            'HTTP_ACCEPT': 'application/json',
            'HTTP_AUTHORIZATION': 'Bearer %s' % token['access_token']
        }
        url = '/api/cat/'
        r = self.client.get(url, **headers)
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.content)
        self.assertEqual(len(data['objects']), 1)
        self.assertEqual(data['objects'][0]['name'], u"Kitty")
