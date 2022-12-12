from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator

class UserSerializer(serializers.Serializer):

    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(min_length=4, max_length=16, validators=[UniqueValidator(queryset=User.objects.all())])
    email = serializers.EmailField(validators= [UniqueValidator(queryset=User.objects.all())])
    password = serializers.CharField(min_length=8, max_length=32, write_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['username'], validated_data['email'], validated_data['password'])
        return user