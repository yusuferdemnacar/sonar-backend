import math
import requests
from rest_framework.response import Response
from rest_framework.views import APIView

from article.schemas import Article


class S2AGSearchView(APIView):

    def get(self, request):
        
        search_query = request.GET.get('search_query', None)
        offset = request.GET.get('offset', None)

        url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={search_query}&limit=25&offset={(int(offset)-1)*25}&fields=externalIds,title,abstract,year,citationCount,referenceCount,fieldsOfStudy,publicationTypes,publicationDate,authors'

        print(url)

        s2ag_response = requests.get(url)
        s2ag_response_data = s2ag_response.json()["data"]

        search_results = []

        for paper in s2ag_response_data:

            if "DOI" in paper["externalIds"].keys():
                DOI = paper["externalIds"]["DOI"]
            else:
                if "ArXiv" in paper["externalIds"].keys():
                    DOI = "10.48550/arXiv." + paper["externalIds"]["ArXiv"]
                    print(DOI)
                else:
                    continue
            
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
            
            search_results.append(article)

        total_page_count = math.ceil(int(s2ag_response.json()['total'])/25)

        response_data = {
            "search_results": search_results,
            "total_page_count": total_page_count,
            "search_query": search_query,
            "offset": offset
        }

        return Response(response_data)
