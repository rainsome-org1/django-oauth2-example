from django.db import models


class Cat(models.Model):
    name = models.CharField(u"Name", max_length=64)

    def __unicode__(self):
        return self.name
