from django.urls import path
from .views import *

urlpatterns = [
    path("build/", BuildGraphView.as_view(), name="build"),
]