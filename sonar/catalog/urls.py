from django.urls import path
from .views import *

urlpatterns = [
    path("base/", CatalogBaseView.as_view(), name="base"),
    path("extension/", CatalogExtensionView.as_view(), name="extension"),
]