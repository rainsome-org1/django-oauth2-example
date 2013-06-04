from django.db import models

from django.contrib.auth import models as auth_models


class ApplicationClient(models.Model):
    client_id = models.CharField(max_length=100, unique=True)
    secret = models.CharField(max_length=100, unique=True)
    allowed_scopes = models.TextField()
    # You might also want to mark a certain set of scopes as default
    # scopes in case the client does not specify any in the authorization
    # SRA Scopes are splitted on spaces
    default_scopes = models.TextField(blank=True, null=True)

    # # max_length and choices depend on which grants you support
    # # Good practise: One grant type by client
    # grant_type_choices = [
    #     ('authorization_code', 'Authorization Code 1'),
    # ]
    # grant_type = models.CharField(max_length=32, choices=grant_type_choices)
    # response_type_choices = [
    #     ('token', u"Token Code")
    # ]
    # response_type = models.CharField(max_length=16, choices=response_type_choices)


    # redirect_uris = models.TextField(blank=True, null=True)

    # # You might also want to mark a certain URI as default in case the
    # # client does not specify any in the authorization
    # default_redirect_uri = models.TextField(blank=True, null=True)

    # Authentication token of the client!

    def __unicode__(self):
        return self.client_id


class ApplicationToken(models.Model):
    application = models.ForeignKey(ApplicationClient)
    user = models.ForeignKey(auth_models.User)
    scopes = models.TextField()
    access_token = models.CharField(max_length=100, unique=True)
    expires_at = models.DateTimeField()
