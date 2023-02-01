from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from article.models import *
from article.serializers import *
from catalog.models import *
import requests
from .neo4j_graph_client import *
import concurrent.futures as cf
from time import time
import os
class RequestValidator():

    def validate(self, required_fields):

        if None in required_fields.values():
            missing_fields = [field_name for field_name in required_fields.keys() if required_fields.get(field_name) is None]
            return Response({'error': 'missing form fields: ' + str(missing_fields)}, status=status.HTTP_400_BAD_REQUEST)

        return None

class PaperRetriever():

    def retrieve_paper(self, article_doi):

        nodes = set()
        edges = set()

        s2ag_article_lookup = "https://api.semanticscholar.org/graph/v1/paper/" + article_doi + "?fields=externalIds,title,abstract,year,citationCount,referenceCount,fieldsOfStudy,publicationTypes,publicationDate,authors,references.externalIds"
        s2ag_article_lookup_response = requests.get(s2ag_article_lookup, headers = {'x-api-key':os.environ.get('S2AG_API_KEY')})
        s2ag_article_lookup_json = s2ag_article_lookup_response.json()

        print(s2ag_article_lookup_response.status_code)

        while s2ag_article_lookup_response.status_code != 200:
            print("Retrying for " + article_doi + " ...")
            s2ag_article_lookup_response = requests.get(s2ag_article_lookup, headers = {'x-api-key':os.environ.get('S2AG_API_KEY')})
            s2ag_article_lookup_json = s2ag_article_lookup_response.json()

        article = Article(
            DOI=article_doi,
            title=s2ag_article_lookup_json.get('title', None),
            abstract=s2ag_article_lookup_json.get('abstract', None),
            year=s2ag_article_lookup_json.get('year', None),
            citation_count=s2ag_article_lookup_json.get('citationCount', None),
            reference_count=s2ag_article_lookup_json.get('referenceCount', None),
            fields_of_study=s2ag_article_lookup_json.get('fieldsOfStudy', None),
            publication_types=s2ag_article_lookup_json.get('publicationTypes', None),
            publication_date=s2ag_article_lookup_json.get('publicationDate', None),
            authors=[author["name"] for author in s2ag_article_lookup_json.get('authors', None)] if s2ag_article_lookup_json.get('authors', None) is not None else None
        )

        nodes.add(article)

        references = s2ag_article_lookup_json.get('references', None)

        for reference in references:

            article_reference_externalIds = reference.get('externalIds', None)

            if article_reference_externalIds is not None:

                article_reference_doi = article_reference_externalIds.get('DOI', None)

                if article_reference_doi is not None:

                    edges.add((article_doi, article_reference_doi, "cites"))

        return (nodes, edges)

class BuildGraphView(APIView):

    permission_classes = (IsAuthenticated,)
    request_validator = RequestValidator()
    paper_retriever = PaperRetriever()
    neo4j_graph_client = Neo4jGraphClient()
    
    def post(self, request):

        start = time()
        
        user = request.user
        catalog_name = request.data.get("catalog_name", None)
        catalog_extention_id = request.data.get("catalog_extention_id", None)

        fields = {
            'catalog_name': catalog_name,
            'catalog_extention_id': catalog_extention_id
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result

        catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()

        if catalog_base is None:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_400_BAD_REQUEST)

        catalog_extention = CatalogExtension.objects.filter(catalog_base=catalog_base, id=catalog_extention_id).first()

        if catalog_extention is None:
            return Response({'error': 'catalog extention not found'}, status=status.HTTP_400_BAD_REQUEST)

        article_doi_set = set()

        for article in catalog_base.article_identifiers.all():
            article_doi_set.add(article.DOI)

        for article in catalog_extention.article_identifiers.all():
            article_doi_set.add(article.DOI)

        nodes = set()
        edges = set()

        with cf.ThreadPoolExecutor(max_workers=100) as executor:
            
            futures = [executor.submit(self.paper_retriever.retrieve_paper, article_doi) for article_doi in article_doi_set]

            for future in cf.as_completed(futures):
                result = future.result()

                nodes = nodes.union(result[0])
                edges = edges.union(result[1])

        edges = list(edges)
        edges = [edge for edge in edges if edge[1] in [node.DOI for node in nodes]]

        print(len(edges))

        data_retrieval_time = time() - start

        print("Data retrieved in " + str(data_retrieval_time) + " seconds")

        print("Building graph ...")

        self.neo4j_graph_client.create_articles_batch(nodes)
        self.neo4j_graph_client.create_edges_batch(edges, batch_size=500)

        graph_building_time = time() - start - data_retrieval_time

        print("Graph built in " + str(graph_building_time) + " seconds")

        return Response({'success': 'graph built'}, status=status.HTTP_200_OK)