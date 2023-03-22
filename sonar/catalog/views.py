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
from neo4j_client import Neo4jClient
from graph.neo4j_service import CatalogService
from .s2ag_service import S2AGService
from graph.models import Citation

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
        
        catalog_base_articles = [article['doi'] for article in self.catalog_service.get_base_articles(user.username, catalog_base_name)]
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
            start = time.time()

            article_in_base = self.catalog_service.check_if_article_in_base(user.username, catalog_base_name, article_doi)

            print("article in base: ", time.time() - t)
            t = time.time()

            if article_in_base:

                return Response({'error': 'article_doi: ' + article_doi + ' already in catalog base: ' + catalog_base_name}, status=status.HTTP_400_BAD_REQUEST)

            print("get articles: ", time.time() - t)
            t = time.time()
            
            existing_articles = self.catalog_service.get_existing_articles([article_doi])

            print("existing articles: ", time.time() - t)
            t = time.time()

            if not existing_articles:

                article_result = self.s2ag_service.get_articles([article_doi])

                if type(article_result) is int:
                    return Response({'error': 'Error while getting article from external source'}, status=status.HTTP_502_BAD_GATEWAY)

                self.catalog_service.create_article_patterns(article_result)

                print("create article pattern: ", time.time() - t)
                t = time.time()
            
            self.catalog_service.add_articles_to_base(user.username, catalog_base_name, [article_doi])

            print("add article to base: ", time.time() - t)
            t = time.time()

            print("total: ", time.time() - start)

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

        catalog_extension_articles = [article['doi'] for article in self.catalog_service.get_extension_articles(user.username, catalog_base_name, catalog_extension_name)]
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
            'catalog_base_name': catalog_base_name,
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
            start = time.time()

            base_articles = self.catalog_service.get_base_articles(user.username, catalog_base_name)

            print("base_articles: ", time.time() - t)
            t = time.time()

            inbound_citation_count = 0
            for article in base_articles:
                inbound_citation_count += article["inbound_citation_count"]

            if inbound_citation_count > 1000:
                return Response({'error': 'too many inbound citations'}, status=status.HTTP_400_BAD_REQUEST)

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

            # split new articles into bundles of 1000
            new_article_bundle_batches = [new_article_bundles[i:i+1000] for i in range(0, len(new_article_bundles), 1000)]

            print("new_article_outbound_citation_dois: ", time.time() - t)
            t = time.time()

            batch = 0

            for new_article_bundle_batch in new_article_bundle_batches:

                print("batch: ", batch)
                batch += 1

                self.catalog_service.create_article_patterns(new_article_bundle_batch)

            print("create_article_patterns: ", time.time() - t)
            t = time.time()
            
            self.catalog_service.add_articles_to_extension(user.username, catalog_base_name, catalog_extension_name, list(inbound_citation_article_dois))

            print("add_article_to_extension: ", time.time() - t)
            t = time.time()

            print("total: ", time.time() - start)

            return Response({"info": "s2ag inbound citations added"}, status=status.HTTP_200_OK)

        elif edit_type == "add_outbound_s2ag_citations":
            
            t = time.time()
            start = time.time()

            base_articles = self.catalog_service.get_base_articles(user.username, catalog_base_name)

            print("base_articles: ", time.time() - t)
            t = time.time()

            outbound_citation_count = 0
            for article in base_articles:
                outbound_citation_count += article["outbound_citation_count"]

            if outbound_citation_count > 1000:
                return Response({'error': 'too many outbound citations'}, status=status.HTTP_400_BAD_REQUEST)
            
            base_article_dois = [article["doi"] for article in base_articles]
            outbound_citation_article_dois = set(self.s2ag_service.get_outbound_citation_article_dois(base_article_dois))

            print("outbound_citation_article_dois: ", time.time() - t)
            t = time.time()

            existing_articles = self.catalog_service.get_existing_articles(outbound_citation_article_dois)
            existing_article_dois = [article["doi"] for article in existing_articles]

            print("existing_article_dois: ", time.time() - t)
            t = time.time()

            new_article_dois = outbound_citation_article_dois - set(existing_article_dois)
            new_article_bundles = self.s2ag_service.get_articles(new_article_dois)

            print("new_articles: ", time.time() - t)
            t = time.time()

            # split new articles into bundles of 1000
            new_article_bundle_batches = [new_article_bundles[i:i+1000] for i in range(0, len(new_article_bundles), 1000)]

            for new_article_bundle_batch in new_article_bundle_batches:

                print("batch: ", batch)
                batch += 1

                self.catalog_service.create_article_patterns(new_article_bundle_batch)

            print("create_article_patterns: ", time.time() - t)
            t = time.time()

            self.catalog_service.add_articles_to_extension(user.username, catalog_base_name, catalog_extension_name, list(outbound_citation_article_dois))

            print("add_article_to_extension: ", time.time() - t)
            t = time.time()

            print("total: ", time.time() - start)

            return Response({"info": "s2ag outbound citations added"}, status=status.HTTP_200_OK)

        elif edit_type == "add_s2ag_paper_id":

            # TODO: this is old code, need to update to new pattern

            # this part is very similar to adding a single paper to a catalog base

            article_doi = request.data.get('article_doi', None)
            
            fields = {
                'article_doi': article_doi
            }

            validation_result = self.request_validator.validate(fields)

            if validation_result:
                return validation_result
            
            article_in_extension = self.catalog_service.check_if_article_in_extension(user.username, catalog_base_name, catalog_extension_name, article_doi)

            if article_in_extension:
                return Response({'error': 'article already in extension'}, status=status.HTTP_400_BAD_REQUEST)
            
            article = self.s2ag_service.get_article(article_doi)

            existing_articles = self.catalog_service.get_existing_articles([article_doi])

            if not existing_articles:

                article_result = self.s2ag_service.get_articles([article_doi])

                if type(article_result) is int:
                    return Response({'error': 'Error while getting article from external source'}, status=status.HTTP_502_BAD_GATEWAY)

                self.catalog_service.create_article_patterns(article_result)

            self.catalog_service.add_articles_to_extension(user.username, catalog_base_name, catalog_extension_name, [article_doi])
            
            return Response({"info": "article with doi: " + article_doi + " added to catalog extension: " + catalog_extension_name}, status=status.HTTP_200_OK)

        elif edit_type == "remove_s2ag_paper_id":

            # TODO: this is old code, need to update to new pattern

            article_doi = request.data.get('article_doi', None)

            fields = {
                'article_doi': article_doi
            }

            validation_result = self.request_validator.validate(fields)

            if validation_result:
                return validation_result
            
            article_in_extension = self.catalog_service.check_if_article_in_extension(user.username, catalog_base_name, catalog_extension_name, article_doi)

            if not article_in_extension:
                return Response({'error': 'article not in extension'}, status=status.HTTP_400_BAD_REQUEST)
            
            self.catalog_service.remove_article_from_extension(user.username, catalog_base_name, catalog_extension_name, article_doi)

            return Response({"info": "article with doi: " + article_doi + " removed from catalog extension: " + catalog_extension_name}, status=status.HTTP_200_OK)

    def delete(self, request):
        
        user = request.user
        catalog_base_name = request.data.get('catalog_base_name', None)
        catalog_extension_name = request.data.get('catalog_extension_name', None)

        fields = {
            'catalog_base_name': catalog_base_name,
            'catalog_extension_name': catalog_extension_name
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result

        catalog_base = self.catalog_service.check_if_base_exists(user.username, catalog_base_name)

        if not catalog_base:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

        catalog_extension = self.catalog_service.check_if_extension_exists(user.username, catalog_base_name, catalog_extension_name)

        if not catalog_extension:
            return Response({'error': 'catalog extension not found'}, status=status.HTTP_404_NOT_FOUND)

        self.catalog_service.delete_extension_node(user.username, catalog_base_name, catalog_extension_name)

        return Response({"info": "catalog extension deleted"}, status=status.HTTP_200_OK)

@api_view(['GET',])
@permission_classes([IsAuthenticated])
def get_all_catalog_bases(request):
    user = request.user
    neo4j_client = Neo4jClient()
    catalog_service = CatalogService(neo4j_client)
    catalog_bases = catalog_service.get_all_catalog_bases_of_user(user.username)

    return Response(catalog_bases, status=status.HTTP_200_OK)

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
    request_validator = RequestValidator()
    neo4j_client = Neo4jClient()
    catalog_service = CatalogService(neo4j_client)

    user = request.user
    catalog_base_name = request.query_params.get('catalog_base_name', None)
    catalog_extension_name = request.query_params.get('catalog_extension_name', None)
    offset = int(request.GET.get('offset', None))
    fields = {
        'catalog_name': catalog_base_name
    }

    validation_result = request_validator.validate(fields)

    if validation_result:
        return validation_result

    catalog_base_exists = catalog_service.check_if_base_exists(user.username, catalog_base_name)

    if not catalog_base_exists:
        return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

    catalog_extension_exists = catalog_service.check_if_extension_exists(user.username, catalog_base_name, catalog_extension_name)

    if not catalog_extension_exists:
        return Response({'error': 'catalog extension not found'}, status=status.HTTP_404_NOT_FOUND)

    catalog_extension_articles_count = catalog_service.get_base_articles_count(user.username, catalog_base_name)
    catalog_extension_articles = catalog_service.get_extension_articles_with_pagination(user.username, catalog_base_name, catalog_extension_name, (offset - 1) * 25, (offset) * 25)
    data = {
    'articles': catalog_extension_articles,
    'total_count': catalog_extension_articles_count,
    'page_count': math.ceil(catalog_extension_articles_count / 25)
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
    request_validator = RequestValidator()
    neo4j_client = Neo4jClient()
    catalog_service = CatalogService(neo4j_client)

    user = request.user
    catalog_base_name = request.query_params.get('catalog_base_name', None)
    offset = int(request.GET.get('offset', None))
    fields = {
        'catalog_name': catalog_base_name
    }

    validation_result = request_validator.validate(fields)

    if validation_result:
        return validation_result

    catalog_base_exists = catalog_service.check_if_base_exists(user.username, catalog_base_name)

    if not catalog_base_exists:
        return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)
    catalog_base_articles_count = catalog_service.get_base_articles_count(user.username, catalog_base_name)
    catalog_base_articles = catalog_service.get_base_articles_with_pagination(user.username, catalog_base_name, (offset - 1) * 25, (offset) * 25)
    data = {
    'articles': catalog_base_articles,
    'total_count': catalog_base_articles_count,
    'page_count': math.ceil(catalog_base_articles_count / 25)
    }

    return Response(data, status=status.HTTP_200_OK)