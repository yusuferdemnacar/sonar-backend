from django.db import models

class S2AGArticleIdentifier(models.Model):
    s2ag_paperID = models.CharField(primary_key=True, max_length=255, null=False, blank=False)

    class Meta:
        verbose_name_plural = "S2AG Article Identifiers"

    def __str__(self):
        return self.s2ag_paperID

class S2AGSearchDisplayArticle(S2AGArticleIdentifier):
    title = models.TextField()
    abstract = models.TextField(null=True)

    class Meta:
        verbose_name_plural = "S2AG Search Display Articles"

    def __str__(self):
        return "/".join(self.s2ag_paperID, self.title)