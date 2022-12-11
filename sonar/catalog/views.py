from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import *
from .models import *

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
            return Response({'error': 'catalog_name is required'}, status=400)

        catalog_base = CatalogBase.objects.create(owner=user, catalog_name=catalog_name)

        catalog_base.save()

        return Response({"info": "catalog base creation successful", "catalog_id": catalog_base.id}, status=200)

    def put(self, request):
        
        user = request.user
        catalog_name = request.data.get('catalog_name', None)
        edit_type = request.data.get('edit_type', None)

        if catalog_name is None:
            return Response({'error': 'catalog_name is required'}, status=400)

        if edit_type is None:
            return Response({'error': 'edit_type is required'}, status=400)

        catalog_base = CatalogBase.objects.filter(owner=user, catalog_name=catalog_name).first()

        if not catalog_base:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

        if edit_type == "add_s2ag_paper_id":

            s2ag_paper_id = request.data.get('s2ag_paper_id', None)

            if s2ag_paper_id is None:
                return Response({'error': 's2ag_paper_id is required'}, status=400)

            s2ag_paper_identifier, _ = S2AGArticleIdentifier.objects.get_or_create(s2ag_paperID=s2ag_paper_id)
            
            catalog_base.s2ag_paper_identifiers.add(s2ag_paper_identifier)

            catalog_base.save()

            return Response({"info": "s2ag_paper_id: " + s2ag_paper_id + " added to catalog base: " + catalog_name}, status=200)

        if edit_type == "remove_s2ag_paper_id":

            s2ag_paper_id = request.data.get('s2ag_paper_id', None)

            if s2ag_paper_id is None:
                return Response({'error': 's2ag_paper_id is required'}, status=400)

            catalog_base_s2ag_paper_identifiers = catalog_base.s2ag_paper_identifiers.all()

            s2ag_paper_identifier = S2AGArticleIdentifier.objects.filter(s2ag_paperID=s2ag_paper_id).first()

            if s2ag_paper_identifier not in catalog_base_s2ag_paper_identifiers:
                return Response({'error': 's2ag_paper_id: ' + s2ag_paper_id + ' not in catalog base'}, status=400)
            
            catalog_base.s2ag_paper_identifiers.remove(s2ag_paper_identifier)

            catalog_base.save()

            return Response({"info": "s2ag_paper_id: " + s2ag_paper_id + " removed from catalog base"}, status=200)

    def delete(self, request):
        pass

class CatalogExtensionView(APIView):

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        pass

    def post(self, request):
        pass

    def put(self, request):
        pass

    def delete(self, request):
        pass
