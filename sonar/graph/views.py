from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from article.models import *
from article.serializers import *
from catalog.models import *
import requests
from neo4j_client import *
class RequestValidator():

    def validate(self, required_fields):

        if None in required_fields.values():
            missing_fields = [field_name for field_name in required_fields.keys() if required_fields.get(field_name) is None]
            return Response({'error': 'missing form fields: ' + str(missing_fields)}, status=status.HTTP_400_BAD_REQUEST)

        return None

class PaperRetriever():

    def retrieve(self, doi):

        article = Article.objects.filter(DOI=doi).first()

        if article is None:
            return Response({'error': 'article not found'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ArticleSerializer(article)

        return Response(serializer.data)

class BuildGraphView(APIView):

    permission_classes = (IsAuthenticated,)
    request_validator = RequestValidator()
    
    def post(self, request):
        
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

        for article_doi in article_doi_set:



            s2ag_article_lookup = "https://api.semanticscholar.org/graph/v1/paper/" + article_doi + "?fields=externalIds,title,abstract,year,citationCount,referenceCount,fieldsOfStudy,publicationTypes,publicationDate,authors"
            s2ag_article_lookup_response = requests.get(s2ag_article_lookup)
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

            offset = 0

            next = True

            while next:

                s2ag_inbound_citations_lookup_url = "https://api.semanticscholar.org/graph/v1/paper/" + article_doi + "/references?fields=externalIds&limit=1000&offset=" + str(offset)
                s2ag_inbound_citations_lookup_response = requests.get(s2ag_inbound_citations_lookup_url)

                print(s2ag_inbound_citations_lookup_response.status_code)
                if s2ag_inbound_citations_lookup_response.status_code == 200:

                    try_cnt = 0

                    s2ag_inbound_citations_lookup_json = s2ag_inbound_citations_lookup_response.json()

                    s2ag_paper_citations = s2ag_inbound_citations_lookup_json.get('data', None)
                    
                    if s2ag_paper_citations is not None:

                        for s2ag_paper_citation in s2ag_paper_citations:

                            s2ag_citing_paper = s2ag_paper_citation.get('citedPaper', None)

                            if s2ag_citing_paper is not None:

                                s2ag_citing_paper_externalIds = s2ag_citing_paper.get('externalIds', None)

                                if s2ag_citing_paper_externalIds is not None:
                                
                                    if "DOI" not in s2ag_citing_paper_externalIds.keys():
                                        continue

                                    s2ag_citing_paper_doi = s2ag_citing_paper_externalIds.get('DOI', None)

                                    if s2ag_citing_paper_doi is not None:

                                        if s2ag_citing_paper_doi in article_doi_set:

                                            edges.add((article_doi, s2ag_citing_paper_doi, "cites"))

                        is_there_next = s2ag_inbound_citations_lookup_json.get('next', None)

                        if is_there_next is not None:
                            offset += 1000
                        else:
                            next = False

        neo4j_client = Neo4jClient()
        neo4j_client.create_articles(nodes)
        neo4j_client.create_relations(edges)

        return Response({'success': 'graph built'}, status=status.HTTP_200_OK)