from rest_framework import serializers
from .models import *
from authmngr.serializers import *
from s2ag.serializers import *

class CatalogBaseSerializer(serializers.Serializer):

    catalog_name = serializers.CharField(max_length=255)
    owner = UserSerializer(many=False)
    s2ag_paper_identifiers = S2AGArticleIdentifierSerializer(many=True)

    class Meta:
        model = CatalogBase
        unique_together = ('owner', 'catalog_name')
        fields = ('owner', 'catalog_name', 's2ag_paper_identifiers')

class CatalogExtensionSerializer(serializers.Serializer):

    catalog_base = CatalogBaseSerializer(many=False)
    s2ag_paper_identifiers = S2AGArticleIdentifierSerializer(many=True)

    class Meta:
        model = CatalogExtension
        unique_together = ('owner', 'catalog_base', 's2ag_paper_identifiers')
        fields = ('catalog_base')