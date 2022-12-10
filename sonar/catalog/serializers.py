from rest_framework import serializers
from .models import *
from authmngr.serializers import *

class CatalogBaseSerializer(serializers.Serializer):

    catalog_name = serializers.CharField(max_length=255)
    owner = UserSerializer(many=False)

    class Meta:
        model = CatalogBase
        unique_together = ('owner', 'catalog_name')
        fields = ('owner', 'catalog_name')