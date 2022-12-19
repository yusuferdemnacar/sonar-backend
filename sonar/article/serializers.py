from rest_framework.serializers import ModelSerializer
from .models import *

class ArticleSerializer(ModelSerializer):
    class Meta:
        model = Article
        fields = '__all__'
