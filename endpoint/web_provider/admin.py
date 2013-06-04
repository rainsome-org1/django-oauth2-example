from django.contrib import admin
from endpoint.web_provider.models import *

admin.site.register(Client)
admin.site.register(Token)
admin.site.register(AuthorizationCode)
