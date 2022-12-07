import math
import requests
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import *
from s2ag.models import *
from s2ag.serializers import *

class S2AGSearchView(APIView):

    def get(self, request):
        
        search_query = request.GET.get('search_query', None)
        offset = request.GET.get('offset', None)

        url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={search_query}&limit=25&offset={(int(offset)-1)*25}&fields=title,year,fieldsOfStudy,abstract'

        s2ag_response = requests.get(url)
        s2ag_response_data = s2ag_response.json()["data"]

        search_results = []

        for paper in s2ag_response_data:
            paper["fieldsOfStudy"] = paper["fieldsOfStudy"][0] if paper["fieldsOfStudy"] else None
            article = S2AGSearchDisplayArticle(title=paper['title'], s2ag_paperID=paper['paperId'], abstract = paper['abstract'])
            search_results.append(S2AGSearchDisplayArticleSerializer(article).data)            

        total_page_count = math.ceil(int(s2ag_response.json()['total'])/25)

        response_data = {
            "search_results": search_results,
            "total_page_count": total_page_count,
            "search_query": search_query,
            "offset": offset
        }

        return Response(response_data)
