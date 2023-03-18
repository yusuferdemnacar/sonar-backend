import math
import os
import time

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import *

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
import requests
from neo4j_client import Neo4jClient
from .neo4j_service import CatalogService
from .s2ag_service import S2AGService

class RequestValidator():

    def validate(self, required_fields):

        if None in required_fields.values():
            missing_fields = [field_name for field_name in required_fields.keys() if required_fields.get(field_name) is None]
            return Response({'error': 'missing form fields: ' + str(missing_fields)}, status=status.HTTP_400_BAD_REQUEST)

        return None

class CatalogBaseView(APIView):

    permission_classes = (IsAuthenticated,)
    request_validator = RequestValidator()
    neo4j_client = Neo4jClient()
    catalog_service = CatalogService(neo4j_client)
    s2ag_service = S2AGService()

    def get(self, request):
        
        user = request.user
        catalog_base_name = request.query_params.get('catalog_base_name', None)

        fields = {
            'catalog_base_name': catalog_base_name
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result

        catalog_base_exists = self.catalog_service.check_if_base_exists(user.username, catalog_base_name)

        if not catalog_base_exists:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)
        
        catalog_base_articles = self.catalog_service.get_base_articles(user.username, catalog_base_name)
        return Response(catalog_base_articles, status=status.HTTP_200_OK)

    def post(self, request):
        
        user = request.user
        catalog_base_name = request.POST.get('catalog_base_name', None)

        fields = {
            'catalog_base_name': catalog_base_name
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result

        catalog_base_exists = self.catalog_service.check_if_base_exists(user.username, catalog_base_name)

        if catalog_base_exists:
            return Response({'error': 'catalog base already exists'}, status=status.HTTP_400_BAD_REQUEST)

        self.catalog_service.create_base_node(user.username, catalog_base_name)

        return Response({"info": "catalog base creation successful"}, status=status.HTTP_200_OK)

    def put(self, request):
        
        user = request.user
        catalog_base_name = request.data.get('catalog_base_name', None)
        edit_type = request.data.get('edit_type', None)

        fields = {
            'catalog_base_name': catalog_base_name,
            'edit_type': edit_type
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result

        catalog_base_exists = self.catalog_service.check_if_base_exists(user.username, catalog_base_name)

        if not catalog_base_exists:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

        if edit_type == "add_article":

            article_doi = request.data.get('article_doi', None)

            fields = {
                'article_doi': article_doi
            }

            validation_result = self.request_validator.validate(fields)

            if validation_result:
                return validation_result
            
            t = time.time()
            
            article_in_base = self.catalog_service.check_if_article_in_base(user.username, catalog_base_name, article_doi)

            print("article in base: ", time.time() - t)
            t = time.time()

            if article_in_base:

                return Response({'error': 'article_doi: ' + article_doi + ' already in catalog base: ' + catalog_base_name}, status=status.HTTP_400_BAD_REQUEST)

            article_result = self.s2ag_service.get_articles([article_doi])

            print("get articles: ", time.time() - t)
            t = time.time()

            if type(article_result) is int:
                return Response({'error': 'Error while getting article from external source'}, status=status.HTTP_502_BAD_GATEWAY)

            # article
            # authors
            # inbound_citations
            # outbound_citations
            # authored_by
            
            existing_articles = self.catalog_service.get_existing_articles([article_doi])

            print("existing articles: ", time.time() - t)
            t = time.time()

            if not existing_articles:

                self.catalog_service.create_article_patterns(article_result)

                print("create article pattern: ", time.time() - t)
                t = time.time()
            
            self.catalog_service.add_article_to_base(user.username, catalog_base_name, article_doi)

            print("add article to base: ", time.time() - t)
            t = time.time()

            return Response({"info": "article with doi: " + article_doi + " added to catalog base: " + catalog_base_name}, status=status.HTTP_200_OK)

        if edit_type == "remove_article":

            article_doi = request.data.get('article_doi', None)

            fields = {
                'article_doi': article_doi
            }

            validation_result = self.request_validator.validate(fields)

            if validation_result:
                return validation_result

            article_in_base = self.catalog_service.check_if_article_in_base(user.username, catalog_base_name, article_doi)

            if not article_in_base:
                return Response({'error': 'article_doi: ' + article_doi + ' not in catalog base: ' + catalog_base_name}, status=status.HTTP_400_BAD_REQUEST)
            
            self.catalog_service.remove_article_from_base(user.username, catalog_base_name, article_doi)


            return Response({"info": "article with doi: " + article_doi + " removed from catalog base: " + catalog_base_name}, status=status.HTTP_200_OK)

    def delete(self, request):
        
        user = request.user
        catalog_base_name = request.data.get('catalog_base_name', None)

        fields = {
            'catalog_base_name': catalog_base_name
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result

        catalog_base_exists = self.catalog_service.check_if_base_exists(user.username, catalog_base_name)

        if not catalog_base_exists:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

        self.catalog_service.delete_base_node(user.username, catalog_base_name)

        return Response({"info": "catalog base deleted"}, status=status.HTTP_200_OK)

class CatalogExtensionView(APIView):

    permission_classes = (IsAuthenticated,)
    request_validator = RequestValidator()
    neo4j_client = Neo4jClient()
    catalog_service = CatalogService(neo4j_client)
    s2ag_service = S2AGService()

    def get(self, request):
        
        user = request.user
        catalog_base_name = request.query_params.get('catalog_base_name', None)
        catalog_extension_name = request.query_params.get('catalog_extension_name', None)

        fields = {
            'catalog_base_name': catalog_base_name,
            'catalog_extension_name': catalog_extension_name,
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result

        catalog_base_exists = self.catalog_service.check_if_base_exists(user.username, catalog_base_name)

        if not catalog_base_exists:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

        catalog_extension_exists = self.catalog_service.check_if_extension_exists(user.username, catalog_base_name, catalog_extension_name)
        
        if not catalog_extension_exists:
            return Response({'error': 'catalog extension not found'}, status=status.HTTP_404_NOT_FOUND)

        catalog_extension_articles = self.catalog_service.get_extension_articles(user.username, catalog_base_name, catalog_extension_name)
        return Response(catalog_extension_articles, status=status.HTTP_200_OK)

    def post(self, request):
        
        user = request.user
        catalog_base_name = request.data.get('catalog_base_name', None)
        catalog_extension_name = request.data.get('catalog_extension_name', None)

        fields = {
            'catalog_base_name': catalog_base_name,
            'catalog_extension_name':catalog_extension_name
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result

        catalog_base_exists = self.catalog_service.check_if_base_exists(user.username, catalog_base_name)

        if not catalog_base_exists:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

        catalog_extension_exists = self.catalog_service.check_if_extension_exists(user.username, catalog_base_name, catalog_extension_name)

        if catalog_extension_exists:
            return Response({'error': 'catalog extension already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        self.catalog_service.create_extension_node(user.username, catalog_base_name, catalog_extension_name)

        return Response({"info": "catalog extension creation successful"}, status=status.HTTP_200_OK)

    def put(self, request):

        user = request.user
        catalog_base_name = request.data.get('catalog_base_name', None)
        catalog_extension_name = request.data.get('catalog_extension_name', None)
        edit_type = request.data.get('edit_type', None)

        fields = {
            'catalog_name': catalog_base_name,
            'catalog_extension_name': catalog_extension_name,
            'edit_type': edit_type
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result

        catalog_base_exists = self.catalog_service.check_if_base_exists(user.username, catalog_base_name)

        if not catalog_base_exists:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

        catalog_extension_exists = self.catalog_service.check_if_extension_exists(user.username, catalog_base_name, catalog_extension_name)

        if not catalog_extension_exists:
            return Response({'error': 'catalog extension not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if edit_type == "add_inbound_s2ag_citations":

            t = time.time()

            base_articles = self.catalog_service.get_base_articles(user.username, catalog_base_name)

            print("base_articles: ", time.time() - t)
            t = time.time()

            base_article_dois = [article["doi"] for article in base_articles]
            inbound_citation_article_dois = set(self.s2ag_service.get_inbound_citation_article_dois(base_article_dois))
            
            print("inbound_citation_article_dois: ", time.time() - t)
            t = time.time()

            existing_articles = self.catalog_service.get_existing_articles(inbound_citation_article_dois)
            existing_article_dois = [article["doi"] for article in existing_articles]

            print("existing_article_dois: ", time.time() - t)
            t = time.time()

            new_article_dois = inbound_citation_article_dois - set(existing_article_dois)
            new_article_bundles = self.s2ag_service.get_articles(new_article_dois)

            print("new_articles: ", time.time() - t)
            t = time.time()

            self.catalog_service.create_article_patterns(new_article_bundles)

            print("create_article_patterns: ", time.time() - t)
            t = time.time()
            
            for article_doi in inbound_citation_article_dois:
                self.catalog_service.add_article_to_extension(user.username, catalog_base_name, catalog_extension_name, article_doi)

            print("add_article_to_extension: ", time.time() - t)
            t = time.time()

            return Response({"info": "s2ag inbound citations added"}, status=status.HTTP_200_OK)

        elif edit_type == "add_outbound_s2ag_citations":
            print("llllolll")
            paper_doi_list = [article_identifier.DOI for article_identifier in catalog_base.article_identifiers.all()]

            s2ag_outbound_citation_articles = set()

            for paper_doi in paper_doi_list:

                offset = 0

                next = True

                while next:
                    print("lay")
                    s2ag_outbound_citations_lookup_url = "https://api.semanticscholar.org/graph/v1/paper/" + paper_doi + "/references?fields=externalIds,title,abstract,year,citationCount,referenceCount,fieldsOfStudy,publicationTypes,publicationDate,authors&limit=1000&offset=" + str(offset)
                    s2ag_outbound_citations_lookup_response = requests.get(s2ag_outbound_citations_lookup_url, {'x-api-key':os.environ.get('S2AG_API_KEY')})

                    if s2ag_outbound_citations_lookup_response.status_code == 200:

                        s2ag_outbound_citations_lookup_json = s2ag_outbound_citations_lookup_response.json()

                        s2ag_paper_citations = s2ag_outbound_citations_lookup_json.get('data', None)
                        
                        if s2ag_paper_citations is not None:

                            for s2ag_paper_citation in s2ag_paper_citations:

                                s2ag_cited_paper = s2ag_paper_citation.get('citedPaper', None)

                                if s2ag_cited_paper is not None:

                                    s2ag_cited_paper_externalIds = s2ag_cited_paper.get('externalIds', None)

                                    if s2ag_cited_paper_externalIds is not None:
                                    
                                        if "DOI" not in s2ag_cited_paper_externalIds.keys():
                                            continue

                                        s2ag_cited_paper_doi = s2ag_cited_paper_externalIds.get('DOI', None)

                                        if s2ag_cited_paper_doi is not None:
                                            s2ag_citing_paper_title = s2ag_cited_paper.get('title', None)
                                            s2ag_citing_paper_abstract = s2ag_cited_paper.get('abstract', None)
                                            s2ag_citing_paper_year = s2ag_cited_paper.get('year', None)
                                            s2ag_citing_paper_citation_count = s2ag_cited_paper.get('citationCount',
                                                                                                     None)
                                            s2ag_citing_paper_reference_count = s2ag_cited_paper.get('referenceCount',
                                                                                                      None)
                                            s2ag_citing_paper_fields_of_study = s2ag_cited_paper.get('fieldsOfStudy',
                                                                                                      None)
                                            s2ag_citing_paper_publication_types = s2ag_cited_paper.get(
                                                'publicationTypes', None)
                                            s2ag_citing_paper_publication_date = s2ag_cited_paper.get(
                                                'publicationDate', None)
                                            s2ag_citing_paper_authors = s2ag_cited_paper.get('authors', None)
                                            if s2ag_citing_paper_authors:
                                                s2ag_citing_paper_authors = [author["name"] for author in s2ag_citing_paper_authors]

                                            s2ag_outbound_citation_articles.add(Article(
                                                DOI=s2ag_cited_paper_doi,
                                                title=s2ag_citing_paper_title,
                                                abstract=s2ag_citing_paper_abstract,
                                                year=s2ag_citing_paper_year,
                                                citation_count=s2ag_citing_paper_citation_count,
                                                reference_count=s2ag_citing_paper_reference_count,
                                                fields_of_study=s2ag_citing_paper_fields_of_study,
                                                publication_types=s2ag_citing_paper_publication_types,
                                                publication_date=s2ag_citing_paper_publication_date,
                                                authors=s2ag_citing_paper_authors))


                        is_there_next = s2ag_outbound_citations_lookup_json.get('next', None)

                        if is_there_next is not None:
                            offset += 1000
                        else:
                            next = False

            created = Article.objects.bulk_create(s2ag_outbound_citation_articles, ignore_conflicts=True)
            catalog_extension.article_identifiers.add(*created)
            print("heere")
            return Response({"info": "s2ag outbound citations added", "catalog_extension": CatalogExtensionSerializer(catalog_extension).data}, status=status.HTTP_200_OK)

        elif edit_type == "add_s2ag_paper_id":
            paper_doi = request.data.get('paper_doi', None)
            title = request.data.get('title', None)
            abstract = request.data.get('abstract', None)
            year = request.data.get('year', None)
            citation_count = request.data.get('citation_count', None)
            reference_count = request.data.get('reference_count', None)
            fields_of_study = request.data.get('fields_of_study', None)
            publication_types = request.data.get('publication_types', None)
            publication_date = request.data.get('publication_date', None)
            authors = request.data.get('authors', None)

            fields = {
                'paper_doi': paper_doi
            }

            validation_result = self.request_validator.validate(fields)

            if validation_result:
                return validation_result

            article, _ = Article.objects.get_or_create(DOI=paper_doi)

            if article in catalog_extension.article_identifiers.all():
                return Response({'error': 'paper_doi: ' + paper_doi + ' already in catalog extension: ' + catalog_extension_name},
                                status=status.HTTP_400_BAD_REQUEST)
            article.title = title
            article.abstract = abstract
            article.year = year
            article.citation_count = citation_count
            article.reference_count = reference_count
            article.fields_of_study = fields_of_study
            article.publication_types = publication_types
            article.publication_date = publication_date
            article.authors = authors
            article.save()

            catalog_extension.article_identifiers.add(article)

            catalog_extension.save()

            return Response({"info": "paper_doi: " + paper_doi + " added to catalog extension: " + catalog_extension_name},
                            status=status.HTTP_200_OK)

        elif edit_type == "remove_s2ag_paper_id":
            print('heres')
            paper_doi = request.data.get('paper_doi', None)

            fields = {
                'paper_doi': paper_doi
            }

            validation_result = self.request_validator.validate(fields)

            if validation_result:
                return validation_result

            catalog_extension_paper_identifiers = catalog_extension.article_identifiers.all()

            paper_identifier = Article.objects.filter(DOI=paper_doi).first()

            if paper_identifier not in catalog_extension_paper_identifiers:
                return Response({'error': 'paper_doi: ' + paper_doi + ' not in catalog extension'},
                                status=status.HTTP_400_BAD_REQUEST)

            catalog_extension.article_identifiers.remove(paper_identifier)

            return Response(status=status.HTTP_200_OK)

    def delete(self, request):
        
        user = request.user
        catalog_name = request.data.get('catalog_name', None)
        catalog_extension_name = request.data.get('catalog_extension_name', None)

        fields = {
            'catalog_name': catalog_name,
            'catalog_extension_name': catalog_extension_name
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result

        catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()

        if not catalog_base:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

        catalog_extension = catalog_base.catalog_extensions.filter(catalog_extension_name=catalog_extension_name).first()

        if not catalog_extension:
            return Response({'error': 'catalog extension not found'}, status=status.HTTP_404_NOT_FOUND)

        catalog_extension.delete()

        return Response({"info": "catalog extension deleted"}, status=status.HTTP_200_OK)

@api_view(['GET',])
@permission_classes([IsAuthenticated])
def get_all_catalog_bases(request):
    user = request.user
    catalog_bases = CatalogBase.objects.filter(owner = user)

    catalog_bases_serialized = CatalogBaseSerializer(catalog_bases, many=True)
    return Response(catalog_bases_serialized.data, status=status.HTTP_200_OK)

@api_view(['GET',])
@permission_classes([IsAuthenticated])
def get_catalog_extensions(request):
    user = request.user
    catalog_name = request.GET.get('catalog_name', None)
    if not catalog_name:
        return Response({'error': 'no catalog base given'}, status=status.HTTP_404_NOT_FOUND)

    catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()

    if not catalog_base:
        return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

    catalog_extensions = CatalogExtension.objects.filter(catalog_base=catalog_base)

    catalog_extensions_serialized = CatalogExtensionSerializer(catalog_extensions, many=True)
    return Response(catalog_extensions_serialized.data, status=status.HTTP_200_OK)

@api_view(['GET',])
@permission_classes([IsAuthenticated])
def get_catalog_extension_articles(request):
    user = request.user
    catalog_name = request.query_params.get('catalog_name', None)
    catalog_extension_name = request.query_params.get('catalog_extension_name', None)

    fields = {
        'catalog_name': catalog_name,
        'catalog_extension_name': catalog_extension_name,
    }


    catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()

    if not catalog_base:
        return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

    catalog_extension = catalog_base.catalog_extensions.filter(catalog_extension_name=catalog_extension_name).first()

    if not catalog_extension:
        return Response({'error': 'catalog extension not found'}, status=status.HTTP_404_NOT_FOUND)

    offset = int(request.GET.get('offset', None))
    article_count = catalog_extension.article_identifiers.count()
    articles = catalog_extension.article_identifiers.all()[((offset-1)*25):((offset)*25)]

    serialized_data = ArticleSerializer(articles, many=True)
    articles = serialized_data.data
    data = {
        'articles': articles,
        'total_count':article_count,
        'page_count':math.ceil(article_count/25)
    }

    return Response(data, status=status.HTTP_200_OK)

@api_view(['GET',])
@permission_classes([IsAuthenticated])
def get_catalog_extension_names(request):
    user = request.user
    catalog_name = request.GET.get('catalog_name', None)
    if not catalog_name:
        return Response({'error': 'no catalog base given'}, status=status.HTTP_404_NOT_FOUND)

    catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()

    if not catalog_base:
        return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

    catalog_extensions = CatalogExtension.objects.filter(catalog_base=catalog_base).values_list('catalog_extension_name', flat=True)


    return Response(catalog_extensions, status=status.HTTP_200_OK)

@api_view(['GET',])
@permission_classes([IsAuthenticated])
def get_catalog_base_articles(request):

    user = request.user
    catalog_name = request.query_params.get('catalog_name', None)
    offset = int(request.GET.get('offset', None))
    fields = {
        'catalog_name': catalog_name
    }


    catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()

    if not catalog_base:
        return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

    article_count = catalog_base.article_identifiers.count()
    articles = catalog_base.article_identifiers.all()[((offset - 1) * 25):((offset) * 25)]

    serialized_data = ArticleSerializer(articles, many=True)
    articles = serialized_data.data
    data = {
    'articles': articles,
    'total_count': article_count,
    'page_count': math.ceil(article_count / 25)
    }

    return Response(data, status=status.HTTP_200_OK)