from django.db import models


class Article(models.Model):
    DOI = models.CharField(max_length=255)
    paperId = models.CharField(max_length=255)
    title = models.TextField()
    abstract = models.TextField(null=True)

    class Meta:
      verbose_name_plural = "articles"

    def __str__(self):
        return self.title