from rest_framework.response import Response
from rest_framework.views import APIView

class AnalysisView(APIView):

    def post(self, request):
        return Response({"message": "Hello, world!"})

# Create your views here.
