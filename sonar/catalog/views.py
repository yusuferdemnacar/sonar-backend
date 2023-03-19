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

                citing_article_dois_queryset = Citation.objects.filter(cited_article_doi=article_doi)
                citing_article_dois = citing_article_dois_queryset.values_list('citing_article_doi', flat=True)

                Citation.objects.bulk_create([Citation(citing_article_doi=article_doi, cited_article_doi=cited_article_doi) for cited_article_doi in article_result[0]['outbound_citation_dois']])

                article_result[0]['inbound_citation_dois'] = list(citing_article_dois)

                self.catalog_service.create_article_patterns(article_result)

                citing_article_dois_queryset.delete()

                print("create article pattern: ", time.time() - t)
                t = time.time()
            
            self.catalog_service.add_article_to_base(user.username, catalog_base_name, article_doi)

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

            new_article_outbound_citation_dois = []
            for new_article_bundle in new_article_bundles:
                print("citing article: ", new_article_bundle["article"]["doi"], "cited article count: ", len(new_article_bundle["outbound_citation_dois"]))
                for outbound_citation_doi in new_article_bundle["outbound_citation_dois"]:
                    new_article_outbound_citation_dois.append(Citation(citing_article_doi=new_article_bundle["article"]["doi"], cited_article_doi=outbound_citation_doi))
            
            print("new_article_outbound_citation_dois: ", time.time() - t)
            t = time.time()

            Citation.objects.bulk_create(new_article_outbound_citation_dois, ignore_conflicts=True)

            print("bulk_create: ", time.time() - t)
            t = time.time()

            batch = 0

            for new_article_bundle_batch in new_article_bundle_batches:

                print("batch: ", batch)
                batch += 1

                citing_article_dois_queryset = Citation.objects.filter(cited_article_doi__in = [new_article_bundle["article"]["doi"] for new_article_bundle in new_article_bundle_batch])
                citing_article_dois = {}

                for cited_article_doi in citing_article_dois_queryset.values_list("cited_article_doi", flat=True).distinct():
                    citing_article_dois[cited_article_doi] = [citing_article_doi for citing_article_doi in citing_article_dois_queryset.filter(cited_article_doi=cited_article_doi).values_list("citing_article_doi", flat=True)]
                
                for new_article_bundle in new_article_bundle_batch:
                    new_article_bundle["inbound_citation_dois"] = citing_article_dois.get(new_article_bundle["article"]["doi"], [])

                self.catalog_service.create_article_patterns(new_article_bundle_batch)

                citing_article_dois_queryset.delete()

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

            new_article_outbound_citation_dois = []
            for new_article_bundle in new_article_bundles:
                print("citing article: ", new_article_bundle["article"]["doi"], "cited article count: ", len(new_article_bundle["outbound_citation_dois"]))
                for outbound_citation_doi in new_article_bundle["outbound_citation_dois"]:
                    new_article_outbound_citation_dois.append(Citation(citing_article_doi=new_article_bundle["article"]["doi"], cited_article_doi=outbound_citation_doi))
            
            Citation.objects.bulk_create(new_article_outbound_citation_dois)

            for new_article_bundle_batch in new_article_bundle_batches:

                citing_article_dois_queryset = Citation.objects.filter(cited_article_doi__in = [new_article_bundle["article"]["doi"] for new_article_bundle in new_article_bundle_batch])
                print("queryset: ", len(citing_article_dois_queryset))
                # create a dictionary of citing article dois to cited article dois

                citing_article_dois = {}

                for cited_article_doi in citing_article_dois_queryset.values_list("cited_article_doi", flat=True).distinct():
                    citing_article_dois[cited_article_doi] = [citing_article_doi for citing_article_doi in citing_article_dois_queryset.filter(cited_article_doi=cited_article_doi).values_list("citing_article_doi", flat=True)]

                for new_article_bundle in new_article_bundle_batch:
                    new_article_bundle["inbound_citation_dois"] = citing_article_dois.get(new_article_bundle["article"]["doi"], [])
                    print("citing article: ", new_article_bundle["article"]["doi"], "cited articles: ", new_article_bundle["inbound_citation_dois"])

                self.catalog_service.create_article_patterns(new_article_bundle_batch)

                citing_article_dois_queryset.delete()

            print("create_article_patterns: ", time.time() - t)
            t = time.time()

            self.catalog_service.add_articles_to_extension(user.username, catalog_base_name, catalog_extension_name, list(outbound_citation_article_dois))

            print("add_article_to_extension: ", time.time() - t)
            t = time.time()

            print("total: ", time.time() - start)

            return Response({"info": "s2ag outbound citations added"}, status=status.HTTP_200_OK)

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