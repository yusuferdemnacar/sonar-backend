from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .neo4j_analysis_client import Neo4jAnalysisClient

class RequestValidator():

    def validate(self, required_fields):

        if None in required_fields.values():
            missing_fields = [field_name for field_name in required_fields.keys() if required_fields.get(field_name) is None]
            return Response({'error': 'missing form fields: ' + str(missing_fields)}, status=status.HTTP_400_BAD_REQUEST)

        return None

class AnalysisView(APIView):

    permission_classes = (IsAuthenticated,)
    neo4j_analysis_client = Neo4jAnalysisClient()
    request_validator = RequestValidator()

    def put(self, request):

        user = request.user
        
        node_type = request.data.get('node_type')
        edge_type = request.data.get('edge_type')
        measure_type = request.data.get('measure_type')

        fields = {
            'node_type': node_type,
            'edge_type': edge_type,
            'measure_type': measure_type
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result
        
        if measure_type == 'betweenness':
            return Response(self.neo4j_analysis_client.calculate_betweenness(user.username, node_type, edge_type))
        else:
            return Response({'error': 'invalid measure type'}, status=status.HTTP_400_BAD_REQUEST)
