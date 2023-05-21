from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from neo4j_client import Neo4jClient
from graph.graph_service import CatalogService
from .analysis_service import CentralityService, TimeSeriesCentralityService

from datetime import datetime, timedelta

class RequestValidator():

    def validate(self, required_fields):

        if None in required_fields.values():
            missing_fields = [field_name for field_name in required_fields.keys() if required_fields.get(field_name) is None]
            return Response({'error': 'missing form fields: ' + str(missing_fields)}, status=status.HTTP_400_BAD_REQUEST)

        return None
    
class CentralityView(APIView):

    def __init__(self):

        self.permission_classes = (IsAuthenticated,)
        self.request_validator = RequestValidator()
        self.neo4j_client = Neo4jClient()
        self.catalog_service = CatalogService(self.neo4j_client)
        self.centrality_service = CentralityService(self.neo4j_client)

    def get_score(self, request, score_function):

        user = request.user

        node_type = request.query_params.get('node_type', None)
        edge_type = request.query_params.get('edge_type', None)
        catalog_base_name = request.query_params.get('catalog_base_name', None)
        catalog_extension_name = request.query_params.get('catalog_extension_name', None)
        if catalog_extension_name == '':
            catalog_extension_name = None
        mandatory_fields = {
            'node_type': node_type,
            'edge_type': edge_type,
            'catalog_base_name': catalog_base_name,
        }

        validation_result = self.request_validator.validate(mandatory_fields)

        if validation_result:
            return validation_result
        
        homogenous_graph_types = {
            ("Author", "COAUTHOR_OF"): "UNDIRECTED",
            ("Article", "CITES"): "DIRECTED",
        }

        if node_type not in [pair[0] for pair in homogenous_graph_types.keys()]:
            return Response({'error': 'invalid node type'}, status=status.HTTP_400_BAD_REQUEST)
        
        if edge_type not in [pair[1] for pair in homogenous_graph_types.keys()]:
            return Response({'error': 'invalid edge type'}, status=status.HTTP_400_BAD_REQUEST)
        
        if (node_type, edge_type) not in homogenous_graph_types.keys():
            return Response({'error': 'invalid node type and edge type combination'}, status=status.HTTP_400_BAD_REQUEST)
        
        catalog_base_exists = self.catalog_service.check_if_base_exists(user.username, catalog_base_name)

        if not catalog_base_exists:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)

        if catalog_extension_name:

            catalog_extension_exists = self.catalog_service.check_if_extension_exists(user.username, catalog_base_name, catalog_extension_name)
        
            if not catalog_extension_exists:
                return Response({'error': 'catalog extension not found'}, status=status.HTTP_404_NOT_FOUND)
        
        scores = self.centrality_service.calculate_centrality(user.username, catalog_base_name, catalog_extension_name, (node_type, edge_type), score_function)

        print(len(scores))
        print(score_function.__name__)
        print(homogenous_graph_types[(node_type, edge_type)])
        print(score_function == self.centrality_service.betweenness_centrality)

        score_type = [key for key in scores[0].keys() if "score" in key][0]
        min_score = scores[-1][score_type]
        max_score = scores[0][score_type]

        if score_function.__name__ == "betweenness_centrality" and homogenous_graph_types[(node_type, edge_type)] == "UNDIRECTED":
            print("here")
            for result in scores:
                result["betweenness_centrality_score"] = (result["betweenness_centrality_score"] - min_score) / (max_score - min_score)

        for score in scores:
            if node_type == "Article":
                score['Article'] = {'doi': score['Article']['doi'],
                         'title': score['Article'].get('title', None),
                         'abstract': score['Article'].get('abstract', None),
                         'year': score['Article'].get('year', None),
                         'citation_count': score['Article'].get('inbound_citation_count', None),
                         'reference_count': score['Article'].get('outbound_citation_count', None),
                         'fields_of_study': score['Article'].get('fields_of_study', None),
                         'publication_types': score['Article'].get('publication_types', None),
                         'publication_date': score['Article'].get('publication_date', None, ),
                         }

        return Response(scores, status=status.HTTP_200_OK)

class BetweennessCentralityView(CentralityView):

    def get(self, request):

        return super().get_score(request, CentralityService.betweenness_centrality)
    
class ClosenessCentralityView(CentralityView):

    def get(self, request):

        return super().get_score(request, CentralityService.closeness_centrality)

class EigenvectorCentralityView(CentralityView):

    def get(self, request):

        return super().get_score(request, CentralityService.eigenvector_centrality)
    
class DegreeCentralityView(CentralityView):

    def get(self, request):

        return super().get_score(request, CentralityService.degree_centrality)
    
class PageRankView(CentralityView):

    def get(self, request):

        return super().get_score(request, CentralityService.page_rank)
    
class ArticleRankView(CentralityView):

    def get(self, request):

        return super().get_score(request, CentralityService.article_rank)
class HarmonicCentralityView(CentralityView):

    def get(self, request):

        return super().get_score(request, CentralityService.harmonic_centrality)
    
class TimeSeriesCentralityView(CentralityView):

    def __init__(self):
            
        super().__init__()
        self.centrality_service = TimeSeriesCentralityService(self.neo4j_client)

    def get_scores(self, request, score_function):

        user = request.user

        node_type = request.query_params.get('node_type', None)
        edge_type = request.query_params.get('edge_type', None)
        catalog_base_name = request.query_params.get('catalog_base_name', None)
        catalog_extension_name = request.query_params.get('catalog_extension_name', None)
        time_series_start_date = request.query_params.get('time_series_start_date', None)
        time_series_end_date = request.query_params.get('time_series_end_date', None)
        if catalog_extension_name == '':
            catalog_extension_name = None
        if time_series_start_date == '':
            time_series_start_date = None
        mandatory_fields = {
            'node_type': node_type,
            'edge_type': edge_type,
            'catalog_base_name': catalog_base_name,
            'time_series_end_date': time_series_end_date,
        }

        validation_result = self.request_validator.validate(mandatory_fields)

        if validation_result:
            return validation_result
        
        homogenous_graph_types = {
            ("Author", "COAUTHOR_OF"): "UNDIRECTED",
            ("Article", "CITES"): "DIRECTED",
        }

        if node_type not in [pair[0] for pair in homogenous_graph_types.keys()]:
            return Response({'error': 'invalid node type'}, status=status.HTTP_400_BAD_REQUEST)
        
        if edge_type not in [pair[1] for pair in homogenous_graph_types.keys()]:
            return Response({'error': 'invalid edge type'}, status=status.HTTP_400_BAD_REQUEST)
        
        if (node_type, edge_type) not in homogenous_graph_types.keys():
            return Response({'error': 'invalid node type and edge type combination'}, status=status.HTTP_400_BAD_REQUEST)
        
        catalog_base_exists = self.catalog_service.check_if_base_exists(user.username, catalog_base_name)

        if not catalog_base_exists:
            return Response({'error': 'catalog base not found'}, status=status.HTTP_404_NOT_FOUND)
        
        catalog_base_articles = self.catalog_service.get_base_articles(user.username, catalog_base_name)
        catalog_publication_dates = [article['publication_date'] for article in catalog_base_articles if 'publication_date' in article.keys()]
        
        if catalog_extension_name:

            catalog_extension_exists = self.catalog_service.check_if_extension_exists(user.username, catalog_base_name, catalog_extension_name)
        
            if not catalog_extension_exists:
                return Response({'error': 'catalog extension not found'}, status=status.HTTP_404_NOT_FOUND)
            
            catalog_extension_articles = self.catalog_service.get_extension_articles(user.username, catalog_base_name, catalog_extension_name)
            catalog_publication_dates.extend([article['publication_date'] for article in catalog_extension_articles])

        catalog_publication_dates = [datetime.strptime(date, '%Y-%m-%d').date() for date in catalog_publication_dates]
        catalog_publication_dates = sorted(catalog_publication_dates)
        time_series_start_date = datetime.strptime(time_series_start_date, '%Y-%m-%d').date() if time_series_start_date else catalog_publication_dates[0]
        time_series_end_date = datetime.strptime(time_series_end_date, '%Y-%m-%d').date()

        if time_series_start_date < catalog_publication_dates[0]:
            time_series_start_date = datetime.strftime(catalog_publication_dates[0], '%Y-%m-%d')
        else:
            time_series_start_date = datetime.strftime(time_series_start_date, '%Y-%m-%d')

        if time_series_end_date > catalog_publication_dates[-1]:
            time_series_end_date = datetime.strftime(catalog_publication_dates[-1] + timedelta(days=120), '%Y-%m-%d')
        else:
            time_series_end_date = datetime.strftime(time_series_end_date, '%Y-%m-%d')
            
        scores = self.centrality_service.calculate_centrality(user.username, catalog_base_name, catalog_extension_name, (node_type, edge_type), score_function, time_series_start_date, time_series_end_date)

        if score_function == self.centrality_service.betweenness_centrality and homogenous_graph_types[(node_type, edge_type)] == "UNDIRECTED":

            for end_date in scores.keys():
                for result in scores[end_date]:
                    result["betweenness_centrality_score"] /= 2

        return scores
    
class TimeSeriesBetweennessCentralityView(TimeSeriesCentralityView):

    def get(self, request):

        return super().get_scores(request, TimeSeriesCentralityService.betweenness_centrality)
    
class TimeSeriesClosenessCentralityView(TimeSeriesCentralityView):

    def get(self, request):

        return super().get_scores(request, TimeSeriesCentralityService.closeness_centrality)
    
class TimeSeriesEigenvectorCentralityView(TimeSeriesCentralityView):

    def get(self, request):

        return super().get_scores(request, TimeSeriesCentralityService.eigenvector_centrality)
    
class TimeSeriesDegreeCentralityView(TimeSeriesCentralityView):

    def get(self, request):

        return super().get_scores(request, TimeSeriesCentralityService.degree_centrality)
    
class TimeSeriesPageRankView(TimeSeriesCentralityView):

    def get(self, request):

        return super().get_scores(request, TimeSeriesCentralityService.page_rank)
    
class TimeSeriesArticleRankView(TimeSeriesCentralityView):

    def get(self, request):

        return super().get_scores(request, TimeSeriesCentralityService.article_rank)
    
class TimeSeriesHarmonicCentralityView(TimeSeriesCentralityView):

    def get(self, request):

        return super().get_scores(request, TimeSeriesCentralityService.harmonic_centrality)

class DiffTimeSeriesCentralityView(TimeSeriesCentralityView):

    def __init__(self):
            
        super().__init__()

    def get_scores(self, request, score_function):

        return super().get_scores(request, score_function)
    
    def get_differetial_scores(self, request, score_function):

        scores = self.get_scores(request, score_function)

        node_type = request.query_params.get('node_type', None)
        edge_type = request.query_params.get('edge_type', None)

        graph_type = (node_type, edge_type)

        differential_scores = {}

        sorted_dates = sorted([datetime.strftime(datetime.strptime(date, '%Y-%m-%d').date(), '%Y-%m-%d') for date in scores.keys()])

        key_index = 0

        for key in sorted_dates:
            differential_scores[key] = []
            for result in scores[key]:
                score_type = ""
                for result_key in result.keys():
                    if "score" in result_key:
                        score_type = result_key
                
                if graph_type == ("Article", "CITES"):

                    doi = result['doi']
                    publication_date = result['publication_date']
                    #TODO: FIX THIS !!! (citation_count and reference_count are not in the same format as the other scores)
                    citation_count = result['citation_count']
                    reference_count = result['reference_count']
                    title = result['title']
                    old_score = 0
                    if doi in [score['doi'] for score in scores[sorted_dates[key_index - 1]]]:
                        old_score = [score[score_type] for score in scores[sorted_dates[key_index - 1]] if score['doi'] == doi][0]
                    differential_scores[key].append({
                        'doi': doi,
                        'publication_date': publication_date,
                        'citation_count': citation_count,
                        'reference_count': reference_count,
                        'title': title,
                        score_type: result[score_type] - old_score
                    })
                
                elif graph_type == ("Author", "COAUTHOR_OF"):

                    author_name = result['name']
                    citation_count = result['citation_count']
                    s2ag_id = result['s2ag_id']
                    h_index = result['h_index']
                    s2ag_url = result['s2ag_url']
                    paper_count = result['paper_count']
                    old_score = 0
                    if s2ag_id in [score['s2ag_id'] for score in scores[sorted_dates[key_index - 1]]]:
                        old_score = [score[score_type] for score in scores[sorted_dates[key_index - 1]] if score['s2ag_id'] == s2ag_id][0]
                    differential_scores[key].append({
                        'name': author_name,
                        'citation_count': citation_count,
                        's2ag_id': s2ag_id,
                        'h_index': h_index,
                        's2ag_url': s2ag_url,
                        'paper_count': paper_count,
                        score_type: result[score_type] - old_score
                    })

            key_index += 1

        return differential_scores

class DiffTimeSeriesBetweennessCentralityView(DiffTimeSeriesCentralityView):

    def get(self, request):

        return super().get_differetial_scores(request, TimeSeriesCentralityService.betweenness_centrality)
    
class DiffTimeSeriesClosenessCentralityView(DiffTimeSeriesCentralityView):

    def get(self, request):

        return super().get_differetial_scores(request, TimeSeriesCentralityService.closeness_centrality)
    
class DiffTimeSeriesEigenvectorCentralityView(DiffTimeSeriesCentralityView):

    def get(self, request):

        return super().get_differetial_scores(request, TimeSeriesCentralityService.eigenvector_centrality)
    
class DiffTimeSeriesDegreeCentralityView(DiffTimeSeriesCentralityView):

    def get(self, request):

        return super().get_differetial_scores(request, TimeSeriesCentralityService.degree_centrality)
    
class DiffTimeSeriesPageRankView(DiffTimeSeriesCentralityView):

    def get(self, request):

        return super().get_differetial_scores(request, TimeSeriesCentralityService.page_rank)
    
class DiffTimeSeriesArticleRankView(DiffTimeSeriesCentralityView):

    def get(self, request):

        return super().get_differetial_scores(request, TimeSeriesCentralityService.article_rank)
    
class DiffTimeSeriesHarmonicCentralityView(DiffTimeSeriesCentralityView):

    def get(self, request):

        return super().get_differetial_scores(request, TimeSeriesCentralityService.harmonic_centrality)