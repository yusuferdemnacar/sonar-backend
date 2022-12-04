from django.urls import path

from .views import HomePageView, SearchResultsView, add_catalog

urlpatterns = [
    path("search/", SearchResultsView, name="search_results"),
    path("", HomePageView.as_view(), name="home"),
    path("search/add_catalog", add_catalog , name="add_catalog"),
]