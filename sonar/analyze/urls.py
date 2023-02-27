from django.urls import path
from .views import *

urlpatterns = [
    path("centrality/betweenness/", BetweennessCentralityView.as_view(), name="betweenness_centrality"),
    path("centrality/closeness/", ClosenessCentralityView.as_view(), name="closeness_centrality"),
    path("centrality/eigenvector/", EigenvectorCentralityView.as_view(), name="eigenvector_centrality"),
    path("centrality/degree/", DegreeCentralityView.as_view(), name="degree_centrality"),
    path("centrality/pagerank/", PageRankView.as_view(), name="pagerank"),
    path("centrality/articlerank/", ArticleRankView.as_view(), name="articlerank"),
    path("centrality/harmonic/", HarmonicCentralityView.as_view(), name="harmonic_centrality"),
]