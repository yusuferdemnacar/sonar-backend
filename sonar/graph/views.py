from rest_framework.decorators import permission_classes, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
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

        article_nodes = set()
        citation_edges = set()

        author_nodes = set()
        authorship_edges = set()

        s2ag_article_lookup = "https://api.semanticscholar.org/graph/v1/paper/" + article_doi + "?fields=externalIds,title,abstract,year,citationCount,referenceCount,fieldsOfStudy,publicationTypes,publicationDate,authors.name,authors.paperCount,authors.citationCount,authors.hIndex,authors.affiliations,references.externalIds"
        s2ag_article_lookup_response = requests.get(s2ag_article_lookup, headers = {'x-api-key':os.environ.get('S2AG_API_KEY')})
        s2ag_article_lookup_json = s2ag_article_lookup_response.json()

        if s2ag_article_lookup_response.status_code == status.HTTP_404_NOT_FOUND:
            return None

        while s2ag_article_lookup_response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
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

        authors = s2ag_article_lookup_json.get('authors', None)

        if authors is not None:
                
            for author in authors:

                author_name = author.get('name', None)

                if author_name is not None:

                    author_paper_count = author.get('paperCount', None)
                    author_citation_count = author.get('citationCount', None)
                    author_h_index = author.get('hIndex', None)
                    author_affiliations = author.get('affiliations', None)

                    author = Author(
                        name=author_name,
                        paper_count=author_paper_count,
                        citation_count=author_citation_count,
                        h_index=author_h_index,
                        affiliations=author_affiliations
                    )

                    author_nodes.add(author)
                    authorship_edges.add((author_name, article_doi, "authored"))

        article_nodes.add(article)

        references = s2ag_article_lookup_json.get('references', None)

        for reference in references:

            article_reference_externalIds = reference.get('externalIds', None)

            if article_reference_externalIds is not None:

                article_reference_doi = article_reference_externalIds.get('DOI', None)

                if article_reference_doi is not None:

                    citation_edges.add((article_doi, article_reference_doi, "cites"))

        return {"article_nodes": article_nodes, "citation_edges": citation_edges, "author_nodes": author_nodes, "authorship_edges": authorship_edges}

class BuildGraphView(APIView):

    permission_classes = (IsAuthenticated,)
    request_validator = RequestValidator()
    paper_retriever = PaperRetriever()
    neo4j_graph_client = Neo4jGraphClient()
    
    def post(self, request):

        start = time()
        
        user = request.user
        catalog_name = request.data.get("catalog_name", None)
        catalog_extension_name = request.data.get("catalog_extension_name", None)

        fields = {
            'catalog_name': catalog_name,
            'catalog_extension_name': catalog_extension_name
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result

        catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()

        if catalog_base is None:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_400_BAD_REQUEST)

        catalog_extension = CatalogExtension.objects.filter(catalog_base=catalog_base, catalog_extension_name=catalog_extension_name).first()

        if catalog_extension is None:
            return Response({'error': 'catalog extention not found'}, status=status.HTTP_400_BAD_REQUEST)

        article_doi_set = set()

        for article in catalog_base.article_identifiers.all():
            article_doi_set.add(article.DOI)

        for article in catalog_extension.article_identifiers.all():
            article_doi_set.add(article.DOI)

        article_nodes = set()
        citation_edges = set()

        author_nodes = set()
        authorship_edges = set()

        print("Retrieving Data ...")

        with cf.ThreadPoolExecutor(max_workers=100) as executor:
            
            futures = [executor.submit(self.paper_retriever.retrieve_paper, article_doi) for article_doi in article_doi_set]

            for future in cf.as_completed(futures):
                result = future.result()

                if result is not None:

                    article_nodes = article_nodes.union(result["article_nodes"])
                    citation_edges = citation_edges.union(result["citation_edges"])
                    author_nodes = author_nodes.union(result["author_nodes"])
                    authorship_edges = authorship_edges.union(result["authorship_edges"])

        citation_edges = list(citation_edges)
        citation_edges = [edge for edge in citation_edges if edge[1] in [node.DOI for node in article_nodes]]

        print("article_nodes: " + str(len(article_nodes)))
        print("citation_edges: " + str(len(citation_edges)))
        print("author_nodes: " + str(len(author_nodes)))
        print("authorship_edges: " + str(len(authorship_edges)))

        data_retrieval_time = time() - start

        print("Data retrieved in " + str(data_retrieval_time) + " seconds")

        print("Building graph ...")

        self.neo4j_graph_client.delete_user_graph(username=user.username)

        self.neo4j_graph_client.create_article_nodes_batch(article_set=article_nodes, username=user.username)
        self.neo4j_graph_client.create_citation_edges_batch(citation_set=citation_edges, batch_size=500, username=user.username)
        self.neo4j_graph_client.create_author_nodes_batch(author_set=author_nodes, username=user.username)
        self.neo4j_graph_client.create_authorship_edges_batch(authorship_set=authorship_edges, batch_size=500, username=user.username)
        self.neo4j_graph_client.create_coauthorship_edges(username=user.username)

        graph_building_time = time() - start - data_retrieval_time

        print("Graph built in " + str(graph_building_time) + " seconds")

        return Response({'success': 'graph built'}, status=status.HTTP_200_OK)

@api_view(['GET',])
@permission_classes([IsAuthenticated])
def get_article(request):
    user = request.user
    neo4j_client = Neo4jClient()

    DOI = request.query_params.get('DOI')
    result = neo4j_client.driver.session().run(f'MATCH (n:Article) WHERE n.DOI=\'{DOI}\' RETURN n')
    data = result.data()

    return Response(data, status=status.HTTP_200_OK)