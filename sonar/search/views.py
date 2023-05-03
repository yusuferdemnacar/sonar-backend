import json
import math
import requests
from rest_framework.response import Response
from rest_framework.views import APIView

from article.schemas import Article


class S2AGSearchView(APIView):

    def post(self, request):
        
        search_query = request.GET.get('search_query', None)
        offset = request.GET.get('offset', None)
        filters = request.data.dict()
        url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={search_query}&limit=25&offset={(int(offset)-1)*25}&fields=externalIds,title,abstract,year,citationCount,referenceCount,fieldsOfStudy,publicationTypes,publicationDate,authors,url,openAccessPdf,venue,publicationVenue,citationStyles'
        publication_types = filters['publicationTypes'].split(',')
        if len(publication_types)>0 and publication_types[0] != '':
            url += f"&publicationTypes={','.join(publication_types)}"
        fields_of_study = filters['fieldsOfStudy'].split(',')
        if len(fields_of_study)>0 and fields_of_study[0] != '':
            url += f"&fieldsOfStudy={','.join(fields_of_study)}"
        if filters['startYear'] or filters['endYear']:
            url += f"&year={filters['startYear'] if filters['startYear'] else ''}-{filters['endYear'] if filters['endYear'] else ''}"
        if filters['venue']:
            url += f"&venue={filters['venue']}"
        s2ag_response = requests.get(url)
        s2ag_response_data = s2ag_response.json()["data"] if 'data' in s2ag_response.json() else []

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
            venue=paper['venue']
            publication_venue = paper["publicationVenue"]
            authors = [author["name"] for author in paper["authors"]]
            bibtex = paper["citationStyles"]

            article = Article(
                doi=DOI,
                title=title,
                abstract=abstract,
                year=year,
                citation_count=citation_count,
                reference_count=reference_count,
                fields_of_study=fields_of_study,
                publication_types=publication_types,
                publication_date=publication_date,
                venue=venue,
                publication_venue=publication_venue["url"] if publication_venue and 'url' in publication_venue else None,
                authors=authors,
                s2ag_url= paper["url"],
                open_access_pdf= paper["openAccessPdf"]['url'] if paper["openAccessPdf"] else None,
                bibtex=bibtex["bibtex"] if bibtex else None
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
