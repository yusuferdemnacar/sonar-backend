from django.urls import path
from .views import *

urlpatterns = [
    path("base/", CatalogBaseView.as_view(), name="base"),
    path("extension/", CatalogExtensionView.as_view(), name="extension"),
    path("base/all/", get_all_catalog_bases, name="base"),
    path("extension/all/", get_catalog_extensions, name="extension"),
    path("extension/articles/", get_catalog_extension_articles, name="extension articles"),
    path("base/articles/", get_catalog_base_articles, name="base articles"),
    path("extension/names/", get_catalog_extension_names, name="extension articles"),
    path("article/", get_article_with_doi, name="article"),
    path("author/", get_author_with_s2ag_id, name="author"),
    path("base/extension/", get_extension_articles_of_catalog_base, name="article"),
]