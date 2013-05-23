# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import requests
import urlparse

from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase

from django.contrib.auth import models as auth_models
from oauth.providers import models as providers_models


class OAuth2SessionTest(LiveServerTestCase):

    def setUp(self):
        self.client_id = 'roger'
        self.code = 'code'
        self.redirect_uri = self.live_server_url + reverse('core_index')
        self.allowed_scopes = ['ham', 'jam']
        self.default_scopes = ['jam']
        # Selected scopes for this test
        self.scopes = ['ham']
        self.grant_type = 'authorization_code'

        self.user = auth_models.User.objects.create(
            username='johndoe',
            email='johndoe@example.com')
        self.user.set_password('password')
        self.user.save()

        self.client = providers_models.Client.objects.create(
            client_id=self.client_id,
            user=self.user,
            grant_type=self.grant_type,
            scopes=' '.join(self.allowed_scopes),
            default_scopes=' '.join(self.default_scopes),
            redirect_uris=self.redirect_uri)

    def test_authorize(self):
        """Manual authorization (w/o requests)"""
        client = requests.session()
        url = reverse('accounts_log_in')
        r = client.get(self.live_server_url + url)
        r = client.post(r.url, data={
            'csrfmiddlewaretoken': client.cookies['csrftoken'],
            'username': self.user.username,
            'password': 'password'
        })
        self.assertEqual(r.status_code, 200)

        url = reverse('providers_authorize')
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scopes': ' '.join(self.scopes),
            'state': 'open'
        }
        # u'http://localhost:8081/oauth/authorize/roger/'
        r = client.get(self.live_server_url + url, params=params)
        self.assertEqual(r.status_code, 200)

        url = reverse('providers_authorization')
        r = client.post(self.live_server_url + url, data={
            'csrfmiddlewaretoken': client.cookies['csrftoken'],
            'scopes': ' '.join(self.scopes),
        })

        # My client handles the query at redirect_uri, extract the code and send it to authentication server
        url = reverse('providers_create_token')
        parsed = urlparse.urlparse(r.url)
        code = urlparse.parse_qs(parsed.query)['code']

        r = client.post(self.live_server_url + url,
            data={
                'grant_type': self.grant_type,
                'code': code,
                'client_id': self.client_id,
                'redirect_uri': self.redirect_uri,
                'state': 'open'
            },
            auth=(self.client_id, 'client_password')
        )
        self.assertEqual(r.status_code, 200)

        data = json.loads(r.content)
        self.assertEqual(data['token_type'], "Bearer")
        self.assertEqual(data['extra'], "creds")
        self.assertIn('access_token', data)
        self.assertIn('refresh_token', data)
        self.assertEqual(data['scope'], ' '.join(self.scopes))
