from rest_framework.serializers import ModelSerializer
from .models import *

class ArticleIdentifierSerializer(ModelSerializer):
    class Meta:
        model = ArticleIdentifier
        fields = '__all__'

class ArticleSerializer(ModelSerializer):
    class Meta:
        model = Article
        fields = '__all__'
