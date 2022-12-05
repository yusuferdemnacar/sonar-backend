from django.contrib import admin
from .models import *

class CatalogBaseAdmin(admin.ModelAdmin):
    list_display = ("catalog_name",)

class CatalogExtensionAdmin(admin.ModelAdmin):
    list_display = ("catalog_base",)

admin.site.register(CatalogBase, CatalogBaseAdmin)
admin.site.register(CatalogExtension, CatalogExtensionAdmin)
