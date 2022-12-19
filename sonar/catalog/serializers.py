from rest_framework import serializers
from .models import *
from authmngr.serializers import *
from article.serializers import *

class CatalogBaseSerializer(serializers.Serializer):

    catalog_name = serializers.CharField(max_length=255)
    owner = UserSerializer(many=False)
    article_identifiers = ArticleIdentifierSerializer(many=True)

    class Meta:
        model = CatalogBase
        unique_together = ('owner', 'catalog_name')
        fields = ('owner', 'catalog_name', 'paper_identifiers')

class CatalogExtensionSerializer(serializers.Serializer):

    catalog_base = CatalogBaseSerializer(many=False)
    article_identifiers = ArticleIdentifierSerializer(many=True)

    class Meta:
        model = CatalogExtension
        unique_together = ('owner', 'catalog_base', 'paper_identifiers')
        fields = ('catalog_base')