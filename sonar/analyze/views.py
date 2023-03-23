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

class BetweennessCentralityView(APIView):

    permission_classes = (IsAuthenticated,)
    neo4j_analysis_client = Neo4jAnalysisClient()
    request_validator = RequestValidator()

    def get(self, request):

        user = request.user
        
        node_type = request.query_params.get('node_type')
        edge_type = request.query_params.get('edge_type')
        catalog_base_name = request.query_params.get('catalog_base_name')
        catalog_extension_name = request.query_params.get('catalog_extension_name')

        fields = {
            'node_type': node_type,
            'edge_type': edge_type,
            'catalog_base_name': catalog_base_name,
            'catalog_extension_name': catalog_extension_name
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result
        
        homogenous_graph_types = [
            ("Author", "COAUTHOR_OF"),
            ("Article", "CITES"),
        ]

        if node_type not in [pair[0] for pair in homogenous_graph_types]:
            return Response({'error': 'invalid node type'}, status=status.HTTP_400_BAD_REQUEST)
        
        print(homogenous_graph_types[:][1])
        
        if edge_type not in [pair[1] for pair in homogenous_graph_types]:
            return Response({'error': 'invalid edge type'}, status=status.HTTP_400_BAD_REQUEST)
        
        if (node_type, edge_type) not in homogenous_graph_types:
            return Response({'error': 'invalid node type and edge type combination'}, status=status.HTTP_400_BAD_REQUEST)

        betweenness = self.neo4j_analysis_client.calculate_betweenness_centrality(user.username, catalog_base_name, catalog_extension_name, (node_type, edge_type))

        return Response(betweenness, status=status.HTTP_200_OK)
    
class ClosenessCentralityView(APIView):

    permission_classes = (IsAuthenticated,)
    neo4j_analysis_client = Neo4jAnalysisClient()
    request_validator = RequestValidator()

    def get(self, request):

        user = request.user
        
        node_type = request.query_params.get('node_type')
        edge_type = request.query_params.get('edge_type')
        catalog_base_name = request.query_params.get('catalog_base_name')
        catalog_extension_name = request.query_params.get('catalog_extension_name')

        fields = {
            'node_type': node_type,
            'edge_type': edge_type,
            'catalog_base_name': catalog_base_name,
            'catalog_extension_name': catalog_extension_name
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result
        
        homogenous_graph_types = [
            ("Author", "COAUTHOR_OF"),
            ("Article", "CITES"),
        ]

        if node_type not in [pair[0] for pair in homogenous_graph_types]:
            return Response({'error': 'invalid node type'}, status=status.HTTP_400_BAD_REQUEST)
        
        if edge_type not in [pair[1] for pair in homogenous_graph_types]:
            return Response({'error': 'invalid edge type'}, status=status.HTTP_400_BAD_REQUEST)
        
        if (node_type, edge_type) not in homogenous_graph_types:
            return Response({'error': 'invalid node type and edge type combination'}, status=status.HTTP_400_BAD_REQUEST)

        closeness = self.neo4j_analysis_client.calculate_closeness_centrality(user.username, catalog_base_name, catalog_extension_name, (node_type, edge_type))

        return Response(closeness, status=status.HTTP_200_OK)
    
class EigenvectorCentralityView(APIView):

    permission_classes = (IsAuthenticated,)
    neo4j_analysis_client = Neo4jAnalysisClient()
    request_validator = RequestValidator()

    def get(self, request):

        user = request.user
        
        node_type = request.query_params.get('node_type')
        edge_type = request.query_params.get('edge_type')
        catalog_base_name = request.query_params.get('catalog_base_name')
        catalog_extension_name = request.query_params.get('catalog_extension_name')

        fields = {
            'node_type': node_type,
            'edge_type': edge_type,
            'catalog_base_name': catalog_base_name,
            'catalog_extension_name': catalog_extension_name
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result
        
        homogenous_graph_types = [
            ("Author", "COAUTHOR_OF"),
            ("Article", "CITES"),
        ]

        if node_type not in [pair[0] for pair in homogenous_graph_types]:
            return Response({'error': 'invalid node type'}, status=status.HTTP_400_BAD_REQUEST)
        
        if edge_type not in [pair[1] for pair in homogenous_graph_types]:
            return Response({'error': 'invalid edge type'}, status=status.HTTP_400_BAD_REQUEST)
        
        if (node_type, edge_type) not in homogenous_graph_types:
            return Response({'error': 'invalid node type and edge type combination'}, status=status.HTTP_400_BAD_REQUEST)

        eigenvector = self.neo4j_analysis_client.calculate_eigenvector_centrality(user.username, catalog_base_name, catalog_extension_name, (node_type, edge_type))

        return Response(eigenvector, status=status.HTTP_200_OK)
    
class DegreeCentralityView(APIView):

    permission_classes = (IsAuthenticated,)
    neo4j_analysis_client = Neo4jAnalysisClient()
    request_validator = RequestValidator()

    def get(self, request):

        user = request.user
        
        node_type = request.query_params.get('node_type')
        edge_type = request.query_params.get('edge_type')
        catalog_base_name = request.query_params.get('catalog_base_name')
        catalog_extension_name = request.query_params.get('catalog_extension_name')

        fields = {
            'node_type': node_type,
            'edge_type': edge_type,
            'catalog_base_name': catalog_base_name,
            'catalog_extension_name': catalog_extension_name
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result
        
        homogenous_graph_types = [
            ("Author", "COAUTHOR_OF"),
            ("Article", "CITES"),
        ]

        if node_type not in [pair[0] for pair in homogenous_graph_types]:
            return Response({'error': 'invalid node type'}, status=status.HTTP_400_BAD_REQUEST)
        
        if edge_type not in [pair[1] for pair in homogenous_graph_types]:
            return Response({'error': 'invalid edge type'}, status=status.HTTP_400_BAD_REQUEST)
        
        if (node_type, edge_type) not in homogenous_graph_types:
            return Response({'error': 'invalid node type and edge type combination'}, status=status.HTTP_400_BAD_REQUEST)

        degree = self.neo4j_analysis_client.calculate_degree_centrality(user.username, catalog_base_name, catalog_extension_name, (node_type, edge_type))

        return Response(degree, status=status.HTTP_200_OK)
    
class PageRankView(APIView):

    permission_classes = (IsAuthenticated,)
    neo4j_analysis_client = Neo4jAnalysisClient()
    request_validator = RequestValidator()

    def get(self, request):

        user = request.user
        
        node_type = request.query_params.get('node_type')
        edge_type = request.query_params.get('edge_type')
        catalog_base_name = request.query_params.get('catalog_base_name')
        catalog_extension_name = request.query_params.get('catalog_extension_name')

        fields = {
            'node_type': node_type,
            'edge_type': edge_type,
            'catalog_base_name': catalog_base_name,
            'catalog_extension_name': catalog_extension_name
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result
        
        homogenous_graph_types = [
            ("Author", "COAUTHOR_OF"),
            ("Article", "CITES"),
        ]

        if node_type not in [pair[0] for pair in homogenous_graph_types]:
            return Response({'error': 'invalid node type'}, status=status.HTTP_400_BAD_REQUEST)
        
        if edge_type not in [pair[1] for pair in homogenous_graph_types]:
            return Response({'error': 'invalid edge type'}, status=status.HTTP_400_BAD_REQUEST)
        
        if (node_type, edge_type) not in homogenous_graph_types:
            return Response({'error': 'invalid node type and edge type combination'}, status=status.HTTP_400_BAD_REQUEST)

        page_rank = self.neo4j_analysis_client.calculate_page_rank(user.username, catalog_base_name, catalog_extension_name, (node_type, edge_type))

        return Response(page_rank, status=status.HTTP_200_OK)
    
class ArticleRankView(APIView):

    permission_classes = (IsAuthenticated,)
    neo4j_analysis_client = Neo4jAnalysisClient()
    request_validator = RequestValidator()

    def get(self, request):

        user = request.user
        
        node_type = request.query_params.get('node_type')
        edge_type = request.query_params.get('edge_type')
        catalog_base_name = request.query_params.get('catalog_base_name')
        catalog_extension_name = request.query_params.get('catalog_extension_name')

        fields = {
            'node_type': node_type,
            'edge_type': edge_type,
            'catalog_base_name': catalog_base_name,
            'catalog_extension_name': catalog_extension_name
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result
        
        homogenous_graph_types = [
            ("Author", "COAUTHOR_OF"),
            ("Article", "CITES"),
        ]

        if node_type not in [pair[0] for pair in homogenous_graph_types]:
            return Response({'error': 'invalid node type'}, status=status.HTTP_400_BAD_REQUEST)
        
        if edge_type not in [pair[1] for pair in homogenous_graph_types]:
            return Response({'error': 'invalid edge type'}, status=status.HTTP_400_BAD_REQUEST)
        
        if (node_type, edge_type) not in homogenous_graph_types:
            return Response({'error': 'invalid node type and edge type combination'}, status=status.HTTP_400_BAD_REQUEST)

        article_rank = self.neo4j_analysis_client.calculate_article_rank(user.username, catalog_base_name, catalog_extension_name, (node_type, edge_type))

        return Response(article_rank, status=status.HTTP_200_OK)
    
# write a class for harmonic centrality, it should be very similar to closeness centrality
# for harmonic centrality

class HarmonicCentralityView(APIView):

    permission_classes = (IsAuthenticated,)
    neo4j_analysis_client = Neo4jAnalysisClient()
    request_validator = RequestValidator()

    def get(self, request):

        user = request.user
        
        node_type = request.query_params.get('node_type')
        edge_type = request.query_params.get('edge_type')
        catalog_base_name = request.query_params.get('catalog_base_name')
        catalog_extension_name = request.query_params.get('catalog_extension_name')

        fields = {
            'node_type': node_type,
            'edge_type': edge_type,
            'catalog_base_name': catalog_base_name,
            'catalog_extension_name': catalog_extension_name
        }

        validation_result = self.request_validator.validate(fields)

        if validation_result:
            return validation_result
        
        homogenous_graph_types = [
            ("Author", "COAUTHOR_OF"),
            ("Article", "CITES"),
        ]

        if node_type not in [pair[0] for pair in homogenous_graph_types]:
            return Response({'error': 'invalid node type'}, status=status.HTTP_400_BAD_REQUEST)
        
        if edge_type not in [pair[1] for pair in homogenous_graph_types]:
            return Response({'error': 'invalid edge type'}, status=status.HTTP_400_BAD_REQUEST)
        
        if (node_type, edge_type) not in homogenous_graph_types:
            return Response({'error': 'invalid node type and edge type combination'}, status=status.HTTP_400_BAD_REQUEST)

        harmonic_centrality = self.neo4j_analysis_client.calculate_harmonic_centrality(user.username, catalog_base_name, catalog_extension_name, (node_type, edge_type))

        return Response(harmonic_centrality, status=status.HTTP_200_OK)