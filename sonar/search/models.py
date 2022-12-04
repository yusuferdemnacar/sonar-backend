from django.db import models
from django.contrib.auth.models import User
from .s2agmodels import *

class CatalogAbstract(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="users_%(class)s")
    s2ag_papers = models.ManyToManyField(S2AGArticleIdentifier, related_name="s2ag_papers_%(class)s")

    class Meta:
        abstract = True

class CatalogBase(CatalogAbstract):
    catalog_name = models.CharField(max_length=255, null=False, blank=False)

class CatalogExtension(CatalogAbstract):
    catalog_base = models.ForeignKey(CatalogBase, on_delete=models.CASCADE, related_name="catalog_extensions")
