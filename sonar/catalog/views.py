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
        pass

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
