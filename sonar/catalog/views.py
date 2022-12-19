from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import *
from .models import *
import requests

class CatalogBaseView(APIView):

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        
        user = request.user
        catalog_name = request.query_params.get('catalog_name', None)
        catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()

        if not catalog_base:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            catalog_base_serialized = CatalogBaseSerializer(instance=catalog_base)
            return Response(catalog_base_serialized.data, status=status.HTTP_200_OK)

    def post(self, request):
        
        user = request.user
        catalog_name = request.POST.get('catalog_name', None)

        if catalog_name is None:
            return Response({'error': 'catalog_name is required'}, status=status.HTTP_400_BAD_REQUEST)

        catalog_base, created = CatalogBase.objects.get_or_create(owner=user, catalog_name=catalog_name)

        if not created:
            return Response({'error': 'catalog base already exists'}, status=status.HTTP_400_BAD_REQUEST)

        catalog_base.save()

        return Response({"info": "catalog base creation successful", "catalog_id": catalog_base.id}, status=status.HTTP_200_OK)

    def put(self, request):
        
        user = request.user
        catalog_name = request.data.get('catalog_name', None)
        edit_type = request.data.get('edit_type', None)

        if catalog_name is None:
            return Response({'error': 'catalog_name is required'}, status=status.HTTP_400_BAD_REQUEST)

        if edit_type is None:
            return Response({'error': 'edit_type is required'}, status=status.HTTP_400_BAD_REQUEST)

        catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()

        if not catalog_base:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

        if edit_type == "add_s2ag_paper_id":

            s2ag_paper_id = request.data.get('s2ag_paper_id', None)

            if s2ag_paper_id is None:
                return Response({'error': 's2ag_paper_id is required'}, status=status.HTTP_400_BAD_REQUEST)

            s2ag_paper_identifier, _ = S2AGArticleIdentifier.objects.get_or_create(s2ag_paperID=s2ag_paper_id)
            
            if s2ag_paper_identifier in catalog_base.s2ag_paper_identifiers.all():
                return Response({'error': 's2ag_paper_id: ' + s2ag_paper_id + ' already in catalog base: ' + catalog_name}, status=status.HTTP_400_BAD_REQUEST)

            catalog_base.s2ag_paper_identifiers.add(s2ag_paper_identifier)

            catalog_base.save()

            return Response({"info": "s2ag_paper_id: " + s2ag_paper_id + " added to catalog base: " + catalog_name}, status=status.HTTP_200_OK)

        if edit_type == "remove_s2ag_paper_id":

            s2ag_paper_id = request.data.get('s2ag_paper_id', None)

            if s2ag_paper_id is None:
                return Response({'error': 's2ag_paper_id is required'}, status=status.HTTP_400_BAD_REQUEST)

            catalog_base_s2ag_paper_identifiers = catalog_base.s2ag_paper_identifiers.all()

            s2ag_paper_identifier = S2AGArticleIdentifier.objects.filter(s2ag_paperID=s2ag_paper_id).first()

            if s2ag_paper_identifier not in catalog_base_s2ag_paper_identifiers:
                return Response({'error': 's2ag_paper_id: ' + s2ag_paper_id + ' not in catalog base'}, status=status.HTTP_400_BAD_REQUEST)
            
            catalog_base.s2ag_paper_identifiers.remove(s2ag_paper_identifier)

            catalog_base.save()

            return Response({"info": "s2ag_paper_id: " + s2ag_paper_id + " removed from catalog base"}, status=status.HTTP_200_OK)

    def delete(self, request):
        
        user = request.user
        catalog_name = request.data.get('catalog_name', None)

        if catalog_name is None:
            return Response({'error': 'catalog_name is required'}, status=status.HTTP_400_BAD_REQUEST)

        catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()

        if not catalog_base:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

        catalog_base.delete()

        return Response({"info": "catalog base deleted"}, status=status.HTTP_200_OK)

class CatalogExtensionView(APIView):

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        
        user = request.user
        catalog_name = request.query_params.get('catalog_name', None)
        catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()
        catalog_extension_id = request.query_params.get('catalog_extension_id', None)

        if not catalog_base:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

        catalog_extension = catalog_base.catalog_extensions.filter(id=catalog_extension_id).first()
        
        if not catalog_extension:
            return Response({'error': 'catalog extension of ' + catalog_name + ' not found'}, status=status.HTTP_404_NOT_FOUND)

        catalog_extension_serialized = CatalogExtensionSerializer(instance=catalog_extension)
        return Response(catalog_extension_serialized.data, status=status.HTTP_200_OK)

    def post(self, request):
        
        user = request.user
        catalog_name = request.data.get('catalog_name', None)
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

        if catalog_name is None:
            return Response({'error': 'catalog_name is required'}, status=status.HTTP_400_BAD_REQUEST)

        if catalog_extension_id is None:
            return Response({'error': 'catalog_extension_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        if edit_type is None:
            return Response({'error': 'edit_type is required'}, status=status.HTTP_400_BAD_REQUEST)

        catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()

        if not catalog_base:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

        catalog_extension = catalog_base.catalog_extensions.filter(id=catalog_extension_id).first()

        if not catalog_extension:
            return Response({'error': 'catalog extension of ' + catalog_name + ' not found'}, status=status.HTTP_404_NOT_FOUND)

        if edit_type == "add_inbound_s2ag_citations":

            s2ag_paper_id_list = [s2ag_paper_identifier.s2ag_paperID for s2ag_paper_identifier in catalog_base.s2ag_paper_identifiers.all()]

            s2ag_inbound_citation_identifiers = set()

            for s2ag_paper_id in s2ag_paper_id_list:

                offset = 0

                next = True

                while next:

                    s2ag_inbound_citations_lookup_url = "https://api.semanticscholar.org/graph/v1/paper/" + s2ag_paper_id + "/citations?fields=paperId&limit=1000&offset=" + str(offset)
                    s2ag_inbound_citations_lookup_response = requests.get(s2ag_inbound_citations_lookup_url)

                    if s2ag_inbound_citations_lookup_response.status_code == 200:

                        s2ag_inbound_citations_lookup_json = s2ag_inbound_citations_lookup_response.json()

                        s2ag_paper_citations = s2ag_inbound_citations_lookup_json.get('data', None)
                        
                        if s2ag_paper_citations is not None:

                            for s2ag_paper_citation in s2ag_paper_citations:

                                s2ag_citing_paper = s2ag_paper_citation.get('citingPaper', None)

                                if s2ag_citing_paper is not None:

                                    s2ag_citing_paper_id = s2ag_citing_paper.get('paperId', None)

                                    if s2ag_citing_paper_id is not None:

                                        s2ag_inbound_citation_identifiers.add(S2AGArticleIdentifier(s2ag_paperID=s2ag_citing_paper_id))

                        is_there_next = s2ag_inbound_citations_lookup_json.get('next', None)

                        if is_there_next is not None:
                            offset += 1000
                        else:
                            next = False

            created = S2AGArticleIdentifier.objects.bulk_create(s2ag_inbound_citation_identifiers, ignore_conflicts=True)
            catalog_extension.s2ag_paper_identifiers.add(*created)

            return Response({"info": "s2ag inbound citations added"}, status=status.HTTP_200_OK)

        if edit_type == "add_outbound_s2ag_citations":
            
            s2ag_paper_id_list = [s2ag_paper_identifier.s2ag_paperID for s2ag_paper_identifier in catalog_base.s2ag_paper_identifiers.all()]

            s2ag_outbound_citation_identifiers = set()

            for s2ag_paper_id in s2ag_paper_id_list:

                offset = 0

                next = True

                while next:

                    s2ag_outbound_citations_lookup_url = "https://api.semanticscholar.org/graph/v1/paper/" + s2ag_paper_id + "/references?fields=paperId&limit=1000&offset=" + str(offset)
                    s2ag_outbound_citations_lookup_response = requests.get(s2ag_outbound_citations_lookup_url)

                    if s2ag_outbound_citations_lookup_response.status_code == 200:

                        s2ag_outbound_citations_lookup_json = s2ag_outbound_citations_lookup_response.json()

                        s2ag_paper_references = s2ag_outbound_citations_lookup_json.get('data', None)
                        
                        if s2ag_paper_references is not None:

                            for s2ag_paper_reference in s2ag_paper_references:

                                s2ag_referenced_paper = s2ag_paper_reference.get('citedPaper', None)

                                if s2ag_referenced_paper is not None:

                                    s2ag_referenced_paper_id = s2ag_referenced_paper.get('paperId', None)

                                    if s2ag_referenced_paper_id is not None:

                                        s2ag_outbound_citation_identifiers.add(S2AGArticleIdentifier(s2ag_paperID=s2ag_referenced_paper_id))

                        is_there_next = s2ag_outbound_citations_lookup_json.get('next', None)

                        if is_there_next is not None:
                            offset += 1000
                        else:
                            next = False

            created = S2AGArticleIdentifier.objects.bulk_create(s2ag_outbound_citation_identifiers, ignore_conflicts=True)
            catalog_extension.s2ag_paper_identifiers.add(*created)

            return Response({"info": "s2ag outbound citations added"}, status=status.HTTP_200_OK)

        if edit_type == "remove_s2ag_paper_id":
            pass

    def delete(self, request):
        
        user = request.user
        catalog_name = request.data.get('catalog_name', None)
        catalog_extension_id = request.data.get('catalog_extension_id', None)

        if catalog_name is None:
            return Response({'error': 'catalog_name is required'}, status=status.HTTP_400_BAD_REQUEST)

        if catalog_extension_id is None:
            return Response({'error': 'catalog_extension_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()

        if not catalog_base:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

        catalog_extension = catalog_base.catalog_extensions.filter(id=catalog_extension_id).first()

        if not catalog_extension:
            return Response({'error': 'catalog extension of ' + catalog_name + ' not found'}, status=status.HTTP_404_NOT_FOUND)

        catalog_extension.delete()

        return Response({"info": "catalog extension deleted"}, status=status.HTTP_200_OK)
