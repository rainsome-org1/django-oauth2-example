from django.contrib import admin
from oauth.providers.models import *

admin.site.register(Client)
admin.site.register(Token)
admin.site.register(AuthorizationCode)
