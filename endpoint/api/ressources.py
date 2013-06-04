# -*- coding: utf-8 -*-
# Copyright (c) 2013 Polyconseil SAS. All rights reserved.

from tastypie.resources import ModelResource

from endpoint.core import models as core_models
from endpoint.api import authentication as api_authentication


class CatResource(ModelResource):

    class Meta:
        queryset = core_models.Cat.objects.all()
        resource_name = 'cat'
        authentication = api_authentication.BackendAuthentication()
