from django.db import models

class Citation(models.Model):

    citing_article_doi = models.CharField(max_length=255, db_index=True)
    cited_article_doi = models.CharField(max_length=255, db_index=True)

    def __str__(self):
        return self.citing_article_doi + " cites " + self.cited_article_doi
    
    class Meta:
        db_table = "citation"
        verbose_name_plural = "Citations"
        unique_together = (("citing_article_doi", "cited_article_doi"),)

# Create your models here.
