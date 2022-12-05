from django.urls import path

from .views import *

urlpatterns = [
    path("search/", SearchResultsView, name="search_results"),
    path("", HomePageView.as_view(), name="home"),
    path("search/add_catalog", add_catalog , name="add_catalog"),
    path("search/create_catalog_base/", createCatalogBase , name="create_catalog_base"),
]