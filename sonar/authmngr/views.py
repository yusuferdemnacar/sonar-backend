from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .serializers import *

class RegisterView(APIView):

    def post(self, request):

        user_serializer = RegisterSerializer(data=request.data)

        if user_serializer.is_valid():
            user = user_serializer.save()
            return Response(data=user_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(data=user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
