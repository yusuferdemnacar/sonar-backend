from django.db import models
from django.contrib.auth.models import User

class ArticleIdentifier(models.Model):
    DOI = models.CharField(primary_key=True, max_length=255, null=False, blank=False)

class CatalogAbstract(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="users_%(class)s")
    papers = models.ManyToManyField(ArticleIdentifier, related_name="papers_%(class)s")

    class Meta:
        abstract = True

class CatalogBase(CatalogAbstract):
    catalog_name = models.CharField(max_length=255, null=False, blank=False)

class CatalogExtension(CatalogAbstract):
    catalog_base = models.ForeignKey(CatalogBase, on_delete=models.CASCADE, related_name="catalog_extensions")
