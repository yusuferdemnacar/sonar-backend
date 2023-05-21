from neo4j_client import Neo4jClient
from datetime import timedelta, datetime

class ProjectionService():

    def __init__(self, neo4j_client: Neo4jClient):
        self.neo4j_client = neo4j_client

    def _get_ids(tx, username, catalog_base_name, catalog_extension_name=None):

        user_id = tx.run("""MATCH (u:User) WHERE u.username = "{username}" RETURN id(u) AS id""".format(username=username)).data()[0]['id']
        catalog_base_id = tx.run("""MATCH (u:User)<-[:OWNED_BY]-(cb:CatalogBase) WHERE u.username = "{username}" AND cb.name = "{catalog_base_name}" RETURN id(cb) AS id""".format(username=username, catalog_base_name=catalog_base_name)).data()[0]['id']
        catalog_extension_id = None if catalog_extension_name is None else tx.run("""MATCH (u:User)<-[:OWNED_BY]-(cb:CatalogBase)<-[:EXTENDS]-(ce:CatalogExtension) WHERE u.username = "{username}" AND cb.name = "{catalog_base_name}" AND ce.name = "{catalog_extension_name}" RETURN id(ce) AS id""".format(username=username, catalog_base_name=catalog_base_name, catalog_extension_name=catalog_extension_name)).data()[0]['id']

        return user_id, catalog_base_id, catalog_extension_id

    def _remove_named_graph(tx, username, catalog_base_name, catalog_extension_name=None):

        if catalog_extension_name is None:

            graph_exists_query = """CALL gds.graph.exists('{username}/{catalog_base_name}') YIELD exists""".format(username=username, catalog_base_name=catalog_base_name)

            if tx.run(graph_exists_query).data()[0]['exists']:
                    
                remove_graph_query = """CALL gds.graph.drop('{username}/{catalog_base_name}')""".format(username=username, catalog_base_name=catalog_base_name)
                tx.run(remove_graph_query)

        else:

            graph_exists_query = """CALL gds.graph.exists('{username}/{catalog_base_name}/{catalog_extension_name}') YIELD exists""".format(username=username, catalog_base_name=catalog_base_name, catalog_extension_name=catalog_extension_name)

            if tx.run(graph_exists_query).data()[0]['exists']:

                remove_graph_query = """CALL gds.graph.drop('{username}/{catalog_base_name}/{catalog_extension_name}')""".format(username=username, catalog_base_name=catalog_base_name, catalog_extension_name=catalog_extension_name)
                tx.run(remove_graph_query)

    def _create_named_graph(tx, username, catalog_base_name, catalog_extension_name=None, graph_type=None, start_date=None, end_date=None):

        catalog_extension_projection = '' if catalog_extension_name is None else '/' + catalog_extension_name
        catalog_extension_pattern = '' if catalog_extension_name is None else '<-[:EXTENDS]-(ce:CatalogExtension)'
        catalog_extension_condition = '' if catalog_extension_name is None else ' AND ce.name = "{catalog_extension_name}"'.format(catalog_extension_name=catalog_extension_name)
        catalog_extension_with = '' if catalog_extension_name is None else ', ce'
        catalog_extension_in_a = '' if catalog_extension_name is None else ' OR (a)-[:IN]->(ce)'
        catalog_extension_in_c = '' if catalog_extension_name is None else ' OR (c)-[:IN]->(ce)'
        catalog_extension_author_in_au1 = '' if catalog_extension_name is None else ' OR (au1)<-[:AUTHORED_BY]-(:Article)-[:IN]->(ce)'
        catalog_extension_author_in_au2 = '' if catalog_extension_name is None else ' OR (au2)<-[:AUTHORED_BY]-(:Article)-[:IN]->(ce)'
        publication_date_condition_a = '' if start_date is None or end_date is None else ' AND (date(a.publication_date) >= date("{start_date}") AND date(a.publication_date) <= date("{end_date}"))'.format(start_date=start_date, end_date=end_date)
        publication_date_condition_c = '' if start_date is None or end_date is None else ' AND (date(c.publication_date) >= date("{start_date}") AND date(c.publication_date) <= date("{end_date}"))'.format(start_date=start_date, end_date=end_date)

        user_id, catalog_base_id, catalog_extension_id = ProjectionService._get_ids(tx, username, catalog_base_name, catalog_extension_name)

        weight_name = 'weight_' + str(user_id) + '_' + str(catalog_base_id) if catalog_extension_id is None else 'weight_' + str(user_id) + '_' + str(catalog_base_id) + '_' + str(catalog_extension_id)

        if graph_type == ('Article', 'CITES'):

            named_graph_query = """CALL gds.graph.project.cypher('{username}/{catalog_base_name}{catalog_extension_projection}',
                    'MATCH (u:User)<-[:OWNED_BY]-(cb:CatalogBase){catalog_extension_pattern}
                    WHERE u.username = "{username}" AND cb.name = "{catalog_base_name}"{catalog_extension_condition}
                    WITH cb{catalog_extension_with}
                    MATCH (a:Article)
                    WHERE ((a)-[:IN]->(cb){catalog_extension_in_a}){publication_date_condition_a}
                    RETURN id(a) AS id',
                    'MATCH (u:User)<-[:OWNED_BY]-(cb:CatalogBase){catalog_extension_pattern}
                    WHERE u.username = "{username}" AND cb.name = "{catalog_base_name}"{catalog_extension_condition}
                    WITH cb{catalog_extension_with}
                    MATCH (a:Article), (c:Article)
                    WHERE (((a)-[:IN]->(cb){catalog_extension_in_a}){publication_date_condition_a}) AND (((c)-[:IN]->(cb){catalog_extension_in_c}){publication_date_condition_c})
                    WITH a, c
                    MATCH (a)-[r:CITES]->(c)
                    RETURN DISTINCT id(a) AS source, id(c) AS target')
                """.format(username=username,
                           catalog_base_name=catalog_base_name,
                           catalog_extension_projection=catalog_extension_projection,
                           catalog_extension_pattern=catalog_extension_pattern,
                           catalog_extension_condition=catalog_extension_condition,
                           catalog_extension_with=catalog_extension_with,
                           catalog_extension_in_a=catalog_extension_in_a,
                           catalog_extension_in_c=catalog_extension_in_c,
                           publication_date_condition_a=publication_date_condition_a,
                           publication_date_condition_c=publication_date_condition_c)
            
        elif graph_type == ('Author', 'COAUTHOR_OF'):
        
            named_graph_query = """CALL gds.graph.project.cypher('{username}/{catalog_base_name}{catalog_extension_projection}',
                    'MATCH (u:User)<-[:OWNED_BY]-(cb:CatalogBase){catalog_extension_pattern}
                    WHERE u.username = "{username}" AND cb.name = "{catalog_base_name}"{catalog_extension_condition}
                    WITH cb{catalog_extension_with}
                    MATCH (a:Article)-[:AUTHORED_BY]->(au:Author)
                    WHERE ((a)-[:IN]->(cb){catalog_extension_in_a}){publication_date_condition_a}
                    RETURN id(au) AS id',
                    'MATCH (u:User)<-[:OWNED_BY]-(cb:CatalogBase){catalog_extension_pattern}
                    WHERE u.username = "{username}" AND cb.name = "{catalog_base_name}"{catalog_extension_condition}
                    WITH cb{catalog_extension_with}
                    MATCH (au1:Author)<-[:AUTHORED_BY]-(a:Article), (au2:Author)<-[:AUTHORED_BY]-(a:Article)
                    WHERE ((a)-[:IN]->(cb){catalog_extension_in_a}){publication_date_condition_a}
                    WITH au1, au2
                    MATCH (au1)-[r:COAUTHOR_OF]-(au2)
                    RETURN DISTINCT id(au1) AS source, id(au2) AS target, r.{weight_name} AS weight')
                """.format(username=username,
                           catalog_base_name=catalog_base_name,
                           catalog_extension_projection=catalog_extension_projection,
                           catalog_extension_pattern=catalog_extension_pattern,
                           catalog_extension_condition=catalog_extension_condition,
                           catalog_extension_in_a=catalog_extension_in_a,
                           catalog_extension_with=catalog_extension_with,
                           catalog_extension_author_in_au1=catalog_extension_author_in_au1,
                           catalog_extension_author_in_au2=catalog_extension_author_in_au2,
                           weight_name=weight_name,
                           publication_date_condition_a=publication_date_condition_a)

        tx.run(named_graph_query)

class CentralityService():

    def __init__(self, neo4j_client: Neo4jClient):
        self.neo4j_client = neo4j_client

    def calculate_centrality(self, username, catalog_base_name, catalog_extension_name=None, graph_type=None, centrality_function=None):

        graph_name = username + '/' + catalog_base_name if catalog_extension_name is None else username + '/' + catalog_base_name + '/' + catalog_extension_name

        with self.neo4j_client.driver.session() as session:
            ProjectionService._create_named_graph(session, username, catalog_base_name, catalog_extension_name, graph_type)
            result = session.execute_read(centrality_function, graph_name, graph_type)
            ProjectionService._remove_named_graph(session, username, catalog_base_name, catalog_extension_name)
            return result
    
    def betweenness_centrality(tx, graph_name, graph_type=None):

        if graph_type == ('Article', 'CITES'):

            betweenness_query = """CALL gds.betweenness.stream('{graph_name}') YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS betweenness_centrality_score ORDER BY score DESC""".format(graph_name=graph_name, node_type=graph_type[0])

        elif graph_type == ('Author', 'COAUTHOR_OF'):

            betweenness_query = """CALL gds.betweenness.stream('{graph_name}', {{relationshipWeightProperty: 'weight'}}) YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS betweenness_centrality_score ORDER BY score DESC""".format(graph_name=graph_name, node_type=graph_type[0])

        return tx.run(betweenness_query).data()
    
    def eigenvector_centrality(tx, graph_name, graph_type):

        if graph_type == ('Article', 'CITES'):

            eigenvector_query = """CALL gds.eigenvector.stream('{graph_name}') YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS eigenvector_centrality_score ORDER BY score DESC""".format(graph_name=graph_name, node_type=graph_type[0])

        elif graph_type == ('Author', 'COAUTHOR_OF'):

            eigenvector_query = """CALL gds.eigenvector.stream('{graph_name}', {{relationshipWeightProperty: 'weight'}}) YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS eigenvector_centrality_score ORDER BY score DESC""".format(graph_name=graph_name, node_type=graph_type[0])
        
        return tx.run(eigenvector_query).data()

    def page_rank(tx, graph_name, graph_type):

        if graph_type == ('Article', 'CITES'):

            pagerank_query = """CALL gds.pageRank.stream('{graph_name}') YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS pagerank_score ORDER BY score DESC""".format(graph_name=graph_name, node_type=graph_type[0])

        elif graph_type == ('Author', 'COAUTHOR_OF'):

            pagerank_query = """CALL gds.pageRank.stream('{graph_name}', {{relationshipWeightProperty: 'weight'}}) YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS pagerank_score ORDER BY score DESC""".format(graph_name=graph_name, node_type=graph_type[0])

        return tx.run(pagerank_query).data()
        
    def degree_centrality(tx, graph_name, graph_type):

        if graph_type == ('Article', 'CITES'):

            degree_query = """CALL gds.degree.stream('{graph_name}') YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS degree_centrality_score ORDER BY score DESC""".format(graph_name=graph_name, node_type=graph_type[0])

        elif graph_type == ('Author', 'COAUTHOR_OF'):

            degree_query = """CALL gds.degree.stream('{graph_name}', {{relationshipWeightProperty: 'weight'}}) YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS degree_centrality_score ORDER BY score DESC""".format(graph_name=graph_name, node_type=graph_type[0])

        return tx.run(degree_query).data()
        
    def article_rank(tx, graph_name, graph_type):

        if graph_type == ('Article', 'CITES'):

            article_rank_query = """CALL gds.articleRank.stream('{graph_name}') YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS article_rank_score ORDER BY score DESC""".format(graph_name=graph_name, node_type=graph_type[0])

        elif graph_type == ('Author', 'COAUTHOR_OF'):

            article_rank_query = """CALL gds.articleRank.stream('{graph_name}', {{relationshipWeightProperty: 'weight'}}) YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS article_rank_score ORDER BY score DESC""".format(graph_name=graph_name, node_type=graph_type[0])

        return tx.run(article_rank_query).data()
        
    def closeness_centrality(tx, graph_name, graph_type):

        closeness_query = """CALL gds.beta.closeness.stream('{graph_name}') YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS closeness_centrality_score ORDER BY score DESC""".format(graph_name=graph_name, node_type=graph_type[0])

        return tx.run(closeness_query).data()
        
    def harmonic_centrality(tx, graph_name, graph_type):
        
        harmonic_query = """CALL gds.alpha.closeness.harmonic.stream('{graph_name}') YIELD nodeId, centrality RETURN gds.util.asNode(nodeId) AS {node_type}, centrality AS harmonic_centrality_score ORDER BY centrality DESC""".format(graph_name=graph_name, node_type=graph_type[0])

        return tx.run(harmonic_query).data()
    
class TimeSeriesCentralityService(CentralityService):

    def calculate_centrality(self, username, catalog_base_name, catalog_extension_name=None, graph_type=None, centrality_function=None, start_date=None, end_date=None, first_date=None, last_date=None):
        
        graph_name = username + '/' + catalog_base_name if catalog_extension_name is None else username + '/' + catalog_base_name + '/' + catalog_extension_name

        with self.neo4j_client.driver.session() as session:
            
            results = {}

            current_end_date = datetime.strptime(start_date, "%Y-%m-%d").date()

            while current_end_date <= datetime.strptime(end_date, "%Y-%m-%d").date():

                print(start_date, datetime.strftime(current_end_date, "%Y-%m-%d")) 

                current_end_date_str = current_end_date.strftime("%Y-%m-%d")
                ProjectionService._create_named_graph(session, username, catalog_base_name, catalog_extension_name, graph_type, first_date, current_end_date_str)
                result = session.execute_read(centrality_function, graph_name, graph_type)

                if graph_type == ('Article', 'CITES'):

                    #TODO: Change the citation and reference keys of this dictionary to inbound_citation_count and outbound_citation_count

                    for result_dict in result:
                        doi = result_dict[graph_type[0]]['doi']
                        publication_date = result_dict[graph_type[0]]['publication_date']
                        citation_count = result_dict[graph_type[0]]['inbound_citation_count']
                        reference_count = result_dict[graph_type[0]]['outbound_citation_count']
                        title = result_dict[graph_type[0]]['title']
                        result_dict.pop(graph_type[0])
                        result_dict['doi'] = doi
                        result_dict['publication_date'] = publication_date
                        result_dict['citation_count'] = citation_count
                        result_dict['reference_count'] = reference_count
                        result_dict['title'] = title

                elif graph_type == ('Author', 'COAUTHOR_OF'):

                    for result_dict in result:
                        author_name = result_dict[graph_type[0]]['name']
                        citation_count = result_dict[graph_type[0]]['citation_count'] if 'citation_count' in result_dict[graph_type[0]] else None
                        s2ag_id = result_dict[graph_type[0]]['s2ag_id']
                        h_index = result_dict[graph_type[0]]['h_index'] if 'h_index' in result_dict[graph_type[0]] else None
                        s2ag_url = result_dict[graph_type[0]]['s2ag_url'] if 's2ag_url' in result_dict[graph_type[0]] else None
                        paper_count = result_dict[graph_type[0]]['paper_count'] if 'paper_count' in result_dict[graph_type[0]] else None
                        result_dict.pop(graph_type[0])
                        result_dict['name'] = author_name
                        result_dict['citation_count'] = citation_count
                        result_dict['s2ag_id'] = s2ag_id
                        result_dict['h_index'] = h_index
                        result_dict['s2ag_url'] = s2ag_url
                        result_dict['paper_count'] = paper_count

                results[datetime.strftime(current_end_date, "%Y-%m-%d")] = result
                ProjectionService._remove_named_graph(session, username, catalog_base_name, catalog_extension_name)

                current_end_date += timedelta(days=120)

            print("Done")

            return results