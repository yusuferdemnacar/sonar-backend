from django.db import models

class Article(models.Model):

    DOI = models.CharField(max_length=255, primary_key=True)

    title = models.TextField()
    abstract = models.TextField()
    year = models.IntegerField()
    citation_count = models.IntegerField()
    reference_count = models.IntegerField()
    field_of_studies = models.ArrayField(models.CharField(max_length=255))
    publication_types = models.ArrayField(models.CharField(max_length=255))
    publication_date = models.DateField()
    authors = models.ArrayField(models.CharField(max_length=255))
    