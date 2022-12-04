from django.db import models
from .models import *

class S2AGArticleIdentifier(ArticleIdentifier):
    s2ag_paperID = models.CharField(unique=True, max_length=255, null=False, blank=False)

class S2AGSearchDisplayArticle(S2AGArticleIdentifier):
    title = models.TextField()
    abstract = models.TextField(null=True)

    class Meta:
        verbose_name_plural = "articles"