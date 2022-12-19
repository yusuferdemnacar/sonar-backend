import math
import requests
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import *
from article.models import *
from article.serializers import *

class S2AGSearchView(APIView):

    def get(self, request):
        
        search_query = request.GET.get('search_query', None)
        offset = request.GET.get('offset', None)

        url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={search_query}&limit=25&offset={(int(offset)-1)*25}&fields=externalIds,title,abstract,year,citationCount,referenceCount,fieldsOfStudy,publicationTypes,publicationDate,authors'

        s2ag_response = requests.get(url)
        s2ag_response_data = s2ag_response.json()["data"]

        search_results = []

        for paper in s2ag_response_data:

            if "DOI" not in paper["externalIds"].keys():
                continue

            DOI = paper["externalIds"]["DOI"]
            title = paper["title"]
            abstract = paper["abstract"]
            year = paper["year"]
            citation_count = paper["citationCount"]
            reference_count = paper["referenceCount"]
            fields_of_study = paper["fieldsOfStudy"]
            publication_types = paper["publicationTypes"]
            publication_date = paper["publicationDate"]
            authors = [author["name"] for author in paper["authors"]]

            article = Article(
                DOI=DOI,
                title=title,
                abstract=abstract,
                year=year,
                citation_count=citation_count,
                reference_count=reference_count,
                fields_of_study=fields_of_study,
                publication_types=publication_types,
                publication_date=publication_date,
                authors=authors
            )
            
            search_results.append(ArticleSerializer(article).data)            

        total_page_count = math.ceil(int(s2ag_response.json()['total'])/25)

        response_data = {
            "search_results": search_results,
            "total_page_count": total_page_count,
            "search_query": search_query,
            "offset": offset
        }

        return Response(response_data)
