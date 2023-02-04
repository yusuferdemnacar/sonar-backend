from django.urls import path
from .views import *

urlpatterns = [
    path("", AnalysisView.as_view(), name="analysis"),
]