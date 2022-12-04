from django.contrib import admin
from .models import *
from .s2agmodels import *

class S2AGArticleAdmin(admin.ModelAdmin):
    list_display = ("title",)

admin.site.register(S2AGSearchDisplayArticle, S2AGArticleAdmin)