from django.db import models
import django.contrib.postgres.fields as pg_fields

class Author(models.Model):

    name = models.CharField(max_length=255, primary_key=True)
    paper_count = models.IntegerField(blank=True, null=True)
    citation_count = models.IntegerField(blank=True, null=True)
    h_index = models.IntegerField(blank=True, null=True)
    affiliations = pg_fields.ArrayField(models.CharField(max_length=255), blank=True, null=True)

    class Meta:
        verbose_name_plural = "Authors"

    def __str__(self):
        return self.name