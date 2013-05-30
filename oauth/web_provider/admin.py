from django.contrib import admin
from oauth.web_provider.models import *

admin.site.register(Client)
admin.site.register(Token)
admin.site.register(AuthorizationCode)
