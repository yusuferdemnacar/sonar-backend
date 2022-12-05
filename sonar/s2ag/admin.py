from django.contrib import admin
from .models import *

class S2AGSearchDisplayArticleAdmin(admin.ModelAdmin):
    list_display = ("title",)

admin.site.register(S2AGSearchDisplayArticle, S2AGSearchDisplayArticleAdmin)
