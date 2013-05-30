# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import requests
import urlparse

from django.contrib.auth import models as auth_models
from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase

from oauth.web_provider import models as web_provider_models


class WebProviderTest(LiveServerTestCase):

    def setUp(self):
        self.live_url = self.live_server_url
        self.client_id = 'roger'
        self.code = 'code'
        self.redirect_uri = self.live_url + reverse('core_index')
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

        self.client = web_provider_models.Client.objects.create(
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
        r = client.get(self.live_url + url, verify=False)
        r = client.post(r.url, data={
            'csrfmiddlewaretoken': client.cookies['csrftoken'],
            'username': self.user.username,
            'password': 'password'
        }, verify=False)
        self.assertEqual(r.status_code, 200)

        url = reverse('web_provider_authorize')
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scopes': ' '.join(self.scopes),
            'state': 'open'
        }
        # u'http://localhost:8081/oauth/authorize/roger/'
        r = client.get(self.live_url + url, params=params, verify=False)
        self.assertEqual(r.status_code, 200)

        url = reverse('web_provider_authorization')
        data = {
            'scopes': ' '.join(self.scopes),
            'csrfmiddlewaretoken': client.cookies['csrftoken']
        }
        r = client.post(self.live_url + url, data=data, verify=False)

        # My client handles the query at redirect_uri, extract the code and send it to authentication server
        url = reverse('web_provider_create_token')
        parsed = urlparse.urlparse(r.url)
        code = urlparse.parse_qs(parsed.query)['code']

        r = client.post(self.live_url + url,
            data={
                'grant_type': self.grant_type,
                'code': code,
                'client_id': self.client_id,
                'redirect_uri': self.redirect_uri,
                'state': 'open'
            },
            auth=(self.client_id, 'client_password'),
            verify=False
        )
        self.assertEqual(r.status_code, 200)

        token = json.loads(r.content)
        self.assertEqual(token['token_type'], "Bearer")
        self.assertEqual(token['extra'], "creds")
        self.assertIn('access_token', token)
        self.assertIn('refresh_token', token)
        self.assertEqual(token['scope'], ' '.join(self.scopes))
