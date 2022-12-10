from rest_framework import serializers
from django.contrib.auth.models import User

class UserSerializer(serializers.Serializer):

    username = serializers.CharField(min_length=4, max_length=16)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, max_length=32, write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['username'], validated_data['email'], validated_data['password'])
        return user