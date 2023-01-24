from django.urls import path
from .views import *

urlpatterns = [
    path("base/", CatalogBaseView.as_view(), name="base"),
    path("extension/", CatalogExtensionView.as_view(), name="extension"),
    path("base/all/", get_all_catalog_bases, name="base"),
    path("extension/all/", get_catalog_extensions, name="extension"),
]