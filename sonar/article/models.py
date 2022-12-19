from django.db import models
import django.contrib.postgres.fields as pg_fields

class Article(models.Model):

    DOI = models.CharField(max_length=255, primary_key=True)

    title = models.TextField(blank=True, null=True)
    abstract = models.TextField(blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    citation_count = models.IntegerField(blank=True, null=True)
    reference_count = models.IntegerField(blank=True, null=True)
    fields_of_study = pg_fields.ArrayField(models.CharField(max_length=255), blank=True, null=True)
    publication_types = pg_fields.ArrayField(models.CharField(max_length=255), blank=True, null=True)
    publication_date = models.DateField(blank=True, null=True)
    authors = pg_fields.ArrayField(models.CharField(max_length=255), blank=True, null=True)
    