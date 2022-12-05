from django.urls import path
from .views import *

urlpatterns = [
    path("s2ag_search/", S2AGSearchView.as_view(), name="s2ag_search"),
]