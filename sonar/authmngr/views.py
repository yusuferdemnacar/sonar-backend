from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from .serializers import *
from graph.neo4j_service import UserService
from neo4j_client import Neo4jClient

class RegisterView(APIView):

    neo4j_client = Neo4jClient()
    user_service = UserService(neo4j_client)

    def post(self, request):

        user_serializer = UserSerializer(data=request.data)

        if user_serializer.is_valid():
            user_serializer.save()
            self.user_service.create_user_node(user_serializer.data['username'])
            return Response(data=user_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(data=user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):

    def post(self, request):

        username = request.data.get('username', None)
        email = request.data.get('email', None)
        password = request.data.get('password', None)

        if password is None:
            return Response({'error': 'Please provide a password.'}, status=status.HTTP_400_BAD_REQUEST)

        if username is not None:
            user = authenticate(username=username, password=password)
        else:
            if email is not None:
                user = authenticate(email=email, password=password)
            else:
                return Response({'error': 'Please provide either username or email.'}, status=status.HTTP_400_BAD_REQUEST)

        if user is not None:
            login(request, user)
            data = {
                'username': user.username,
                'email': user.email,
                'token': Token.objects.get_or_create(user=user)[0].key
            }
            return Response(data=data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid Credentials.'}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):

    permission_classes = (IsAuthenticated,)

    def get(self, request):

        request.user.auth_token.delete()
        logout(request)
        return Response(status=status.HTTP_200_OK)
        