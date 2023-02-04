from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import *
from .models import *
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
import requests

class RequestValidator():

    def validate(self, required_fields):

        if None in required_fields.values():
            missing_fields = [field_name for field_name in required_fields.keys() if required_fields.get(field_name) is None]
            return Response({'error': 'missing form fields: ' + str(missing_fields)}, status=status.HTTP_400_BAD_REQUEST)

        return None

class CatalogBaseView(APIView):

    permission_classes = (IsAuthenticated,)
    request_validator = RequestValidator()

    def get(self, request):
        
        user = request.user
        catalog_name = request.query_params.get('catalog_name', None)

        fields = {
            'catalog_name': catalog_name
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result

        catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()

        if not catalog_base:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)
        
        catalog_base_serialized = CatalogBaseSerializer(instance=catalog_base)
        return Response(catalog_base_serialized.data, status=status.HTTP_200_OK)

    def post(self, request):
        
        user = request.user
        print(request.POST)
        catalog_name = request.POST.get('catalog_name', None)

        fields = {
            'catalog_name': catalog_name
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result

        catalog_base, created = CatalogBase.objects.get_or_create(owner=user, catalog_name=catalog_name)

        if not created:
            return Response({'error': 'catalog base already exists'}, status=status.HTTP_400_BAD_REQUEST)

        catalog_base.save()

        return Response({"info": "catalog base creation successful", "catalog_id": catalog_base.id}, status=status.HTTP_200_OK)

    def put(self, request):
        
        user = request.user
        catalog_name = request.data.get('catalog_name', None)
        edit_type = request.data.get('edit_type', None)

        fields = {
            'catalog_name': catalog_name,
            'edit_type': edit_type
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result

        catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()

        if not catalog_base:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

        if edit_type == "add_paper_doi":

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
            
            if article in catalog_base.article_identifiers.all():
                return Response({'error': 'paper_doi: ' + paper_doi + ' already in catalog base: ' + catalog_name}, status=status.HTTP_400_BAD_REQUEST)
            article.title=title
            article.abstract=abstract
            article.year=year
            article.citation_count=citation_count
            article.reference_count=reference_count
            article.fields_of_study=fields_of_study
            article.publication_types=publication_types
            article.publication_date=publication_date
            article.authors=authors
            article.save()

            catalog_base.article_identifiers.add(article)

            catalog_base.save()

            return Response({"info": "paper_doi: " + paper_doi + " added to catalog base: " + catalog_name}, status=status.HTTP_200_OK)

        if edit_type == "remove_paper_doi":

            paper_doi = request.data.get('paper_doi', None)

            fields = {
                'paper_doi': paper_doi
            }

            validation_result = self.request_validator.validate(fields)

            if validation_result:
                return validation_result

            catalog_base_paper_identifiers = catalog_base.article_identifiers.all()

            paper_identifier = Article.objects.filter(DOI=paper_doi).first()

            if paper_identifier not in catalog_base_paper_identifiers:
                return Response({'error': 'paper_doi: ' + paper_doi + ' not in catalog base'}, status=status.HTTP_400_BAD_REQUEST)
            
            catalog_base.article_identifiers.remove(paper_identifier)

            catalog_base.save()

            return Response({"info": "paper_doi: " + paper_doi + " removed from catalog base"}, status=status.HTTP_200_OK)

    def delete(self, request):
        
        user = request.user
        catalog_name = request.data.get('catalog_name', None)

        fields = {
            'catalog_name': catalog_name
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result

        catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()

        if not catalog_base:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

        catalog_base.delete()

        return Response({"info": "catalog base deleted"}, status=status.HTTP_200_OK)

class CatalogExtensionView(APIView):

    permission_classes = (IsAuthenticated,)
    request_validator = RequestValidator()

    def get(self, request):
        
        user = request.user
        catalog_name = request.query_params.get('catalog_name', None)
        catalog_extension_id = request.query_params.get('catalog_extension_id', None)

        fields = {
            'catalog_name': catalog_name,
            'catalog_extension_id': catalog_extension_id
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result

        catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()

        if not catalog_base:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

        catalog_extension = catalog_base.catalog_extensions.filter(id=catalog_extension_id).first()
        
        if not catalog_extension:
            return Response({'error': 'catalog extension not found'}, status=status.HTTP_404_NOT_FOUND)

        catalog_extension_serialized = CatalogExtensionSerializer(instance=catalog_extension)
        return Response(catalog_extension_serialized.data, status=status.HTTP_200_OK)

    def post(self, request):
        
        user = request.user
        catalog_name = request.data.get('catalog_name', None)

        fields = {
            'catalog_name': catalog_name
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result

        catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()

        if not catalog_base:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

        catalog_extension = CatalogExtension.objects.create(catalog_base=catalog_base)

        catalog_extension.save()

        return Response({"info": "catalog extension creation successful", "catalog_extension_id": catalog_extension.id}, status=status.HTTP_200_OK)

    def put(self, request):
        
        user = request.user
        catalog_name = request.data.get('catalog_name', None)
        catalog_extension_id = request.data.get('catalog_extension_id', None)
        edit_type = request.data.get('edit_type', None)

        fields = {
            'catalog_name': catalog_name,
            'catalog_extension_id': catalog_extension_id,
            'edit_type': edit_type
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result

        catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()

        if not catalog_base:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

        catalog_extension = catalog_base.catalog_extensions.filter(id=catalog_extension_id).first()

        if not catalog_extension:
            return Response({'error': 'catalog extension not found'}, status=status.HTTP_404_NOT_FOUND)

        if edit_type == "add_inbound_s2ag_citations":

            paper_doi_list = [article_identifier.DOI for article_identifier in catalog_base.article_identifiers.all()]

            s2ag_inbound_citation_articles = set()

            for paper_doi in paper_doi_list:

                offset = 0

                next = True

                while next:

                    s2ag_inbound_citations_lookup_url = "https://api.semanticscholar.org/graph/v1/paper/" + paper_doi + "/citations?fields=externalIds,title,abstract,year,citationCount,referenceCount,fieldsOfStudy,publicationTypes,publicationDate,authors&limit=1000&offset=" + str(offset)
                    s2ag_inbound_citations_lookup_response = requests.get(s2ag_inbound_citations_lookup_url)

                    if s2ag_inbound_citations_lookup_response.status_code == 200:

                        s2ag_inbound_citations_lookup_json = s2ag_inbound_citations_lookup_response.json()

                        s2ag_paper_citations = s2ag_inbound_citations_lookup_json.get('data', None)
                        
                        if s2ag_paper_citations is not None:

                            for s2ag_paper_citation in s2ag_paper_citations:

                                s2ag_citing_paper = s2ag_paper_citation.get('citingPaper', None)

                                if s2ag_citing_paper is not None:

                                    s2ag_citing_paper_externalIds = s2ag_citing_paper.get('externalIds', None)

                                    if s2ag_citing_paper_externalIds is not None:
                                    
                                        if "DOI" not in s2ag_citing_paper_externalIds.keys():
                                            continue

                                        s2ag_citing_paper_doi = s2ag_citing_paper_externalIds.get('DOI', None)

                                        if s2ag_citing_paper_doi is not None:
                                            s2ag_citing_paper_title = s2ag_citing_paper.get('title', None)
                                            s2ag_citing_paper_abstract = s2ag_citing_paper.get('abstract', None)
                                            s2ag_citing_paper_year = s2ag_citing_paper.get('year', None)
                                            s2ag_citing_paper_citation_count = s2ag_citing_paper.get('citation_count', None)
                                            s2ag_citing_paper_reference_count = s2ag_citing_paper.get('reference_count', None)
                                            s2ag_citing_paper_fields_of_study = s2ag_citing_paper.get('fields_of_study', None)
                                            s2ag_citing_paper_publication_types = s2ag_citing_paper.get('publication_types', None)
                                            s2ag_citing_paper_publication_date = s2ag_citing_paper.get('publication_date', None)
                                            s2ag_citing_paper_authors = s2ag_citing_paper.get('authors', None)

                                            s2ag_inbound_citation_articles.add(Article(
                                            DOI=s2ag_citing_paper_doi,
                                            title=s2ag_citing_paper_title,
                                            abstract=s2ag_citing_paper_abstract,
                                            year=s2ag_citing_paper_year,
                                            citation_count=s2ag_citing_paper_citation_count,
                                            reference_count=s2ag_citing_paper_reference_count,
                                            fields_of_study=s2ag_citing_paper_fields_of_study,
                                            publication_types=s2ag_citing_paper_publication_types,
                                            publication_date=s2ag_citing_paper_publication_date,
                                            authors=s2ag_citing_paper_authors))

                        is_there_next = s2ag_inbound_citations_lookup_json.get('next', None)

                        if is_there_next is not None:
                            offset += 1000
                        else:
                            next = False

            created = Article.objects.bulk_create(s2ag_inbound_citation_articles, ignore_conflicts=True)
            catalog_extension.article_identifiers.add(*created)

            return Response({"info": "s2ag inbound citations added"}, status=status.HTTP_200_OK)

        elif edit_type == "add_outbound_s2ag_citations":

            paper_doi_list = [article_identifier.DOI for article_identifier in catalog_base.article_identifiers.all()]

            s2ag_outbound_citation_articles = set()

            for paper_doi in paper_doi_list:

                offset = 0

                next = True

                while next:

                    s2ag_outbound_citations_lookup_url = "https://api.semanticscholar.org/graph/v1/paper/" + paper_doi + "/references?fields=externalIds,title,abstract,year,citationCount,referenceCount,fieldsOfStudy,publicationTypes,publicationDate,authors&limit=1000&offset=" + str(offset)
                    s2ag_outbound_citations_lookup_response = requests.get(s2ag_outbound_citations_lookup_url)

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
                                            s2ag_citing_paper_citation_count = s2ag_cited_paper.get('citation_count',
                                                                                                     None)
                                            s2ag_citing_paper_reference_count = s2ag_cited_paper.get('reference_count',
                                                                                                      None)
                                            s2ag_citing_paper_fields_of_study = s2ag_cited_paper.get('fields_of_study',
                                                                                                      None)
                                            s2ag_citing_paper_publication_types = s2ag_cited_paper.get(
                                                'publication_types', None)
                                            s2ag_citing_paper_publication_date = s2ag_cited_paper.get(
                                                'publication_date', None)
                                            s2ag_citing_paper_authors = s2ag_cited_paper.get('authors', None)

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

            return Response({"info": "s2ag outbound citations added"}, status=status.HTTP_200_OK)

        if edit_type == "remove_s2ag_paper_id":
            pass

    def delete(self, request):
        
        user = request.user
        catalog_name = request.data.get('catalog_name', None)
        catalog_extension_id = request.data.get('catalog_extension_id', None)

        fields = {
            'catalog_name': catalog_name,
            'catalog_extension_id': catalog_extension_id
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result

        catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()

        if not catalog_base:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

        catalog_extension = catalog_base.catalog_extensions.filter(id=catalog_extension_id).first()

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