from django.contrib import admin
from .models import *

class S2AGSearchDisplayArticleAdmin(admin.ModelAdmin):
    list_display = ("title",)

class S2AGArticleIdentifierAdmin(admin.ModelAdmin):
    list_display = ("s2ag_paperID",)

admin.site.register(S2AGSearchDisplayArticle, S2AGSearchDisplayArticleAdmin)
admin.site.register(S2AGArticleIdentifier, S2AGArticleIdentifierAdmin)
