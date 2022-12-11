from django.db import models
from django.contrib.auth.models import User
from s2ag.models import *

class CatalogAbstract(models.Model):
    s2ag_paper_identifiers = models.ManyToManyField(S2AGArticleIdentifier, related_name="s2ag_papers_%(class)s")

    class Meta:
        abstract = True

class CatalogBase(CatalogAbstract):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="users_%(class)s")
    catalog_name = models.CharField(max_length=255, null=False, blank=False)

    class Meta:
        unique_together = ('owner', 'catalog_name')

class CatalogExtension(CatalogAbstract):
    catalog_base = models.ForeignKey(CatalogBase, on_delete=models.CASCADE, related_name="catalog_extensions")