from django.db import models
from django.contrib.auth.models import User
from article.models import *

class CatalogAbstract(models.Model):
    article_identifiers = models.ManyToManyField(Article, related_name="papers_%(class)s")

    class Meta:
        abstract = True

class CatalogBase(CatalogAbstract):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="users_%(class)s")
    catalog_name = models.CharField(max_length=255, null=False, blank=False)

    class Meta:
        unique_together = ('owner', 'catalog_name')

    def __str__(self):
        return "/".join([self.owner.username, self.catalog_name])

class CatalogExtension(CatalogAbstract):
    catalog_extension_name = models.CharField(max_length=100, null=True,blank=True)
    catalog_base = models.ForeignKey(CatalogBase, on_delete=models.CASCADE, related_name="catalog_extensions")

    def __str__(self):
        return "/".join([str(self.catalog_base), str(self.id)])