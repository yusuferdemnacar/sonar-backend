from rest_framework.serializers import ModelSerializer
from .models import *

class S2AGSearchDisplayArticleSerializer(ModelSerializer):
    class Meta:
        model = S2AGSearchDisplayArticle
        fields = '__all__'