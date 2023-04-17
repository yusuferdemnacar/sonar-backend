from neo4j_client import Neo4jClient

class ProjectionService():

    def __init__(self, neo4j_client: Neo4jClient):
        self.neo4j_client = neo4j_client

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

    def _create_named_graph(tx, username, catalog_base_name, catalog_extension_name=None, graph_type=None):

        if catalog_extension_name is None:

            if graph_type == ('Article', 'CITES'):

                named_graph_query = """CALL gds.graph.project.cypher('{username}/{catalog_base_name}',
                    'MATCH (u:User)<-[:OWNED_BY]-(cb:CatalogBase)
                    WHERE u.username = "{username}" AND cb.name = "{catalog_base_name}"
                    WITH cb
                    MATCH (a:Article)
                    WHERE (a)-[:IN]->(cb)
                    RETURN id(a) AS id',
                    'MATCH (u:User)<-[:OWNED_BY]-(cb:CatalogBase)
                    WHERE u.username = "{username}" AND cb.name = "{catalog_base_name}"
                    WITH cb
                    MATCH (a:Article), (c:Article)
                    WHERE ((a)-[:IN]->(cb)) AND ((c)-[:IN]->(cb))
                    WITH a, c
                    MATCH (a)-[r:CITES]-(c)
                    RETURN DISTINCT id(a) AS source, id(c) AS target, type(r) AS type')
                """.format(username=username, catalog_base_name=catalog_base_name)

                tx.run(named_graph_query)

            elif graph_type == ('Author', 'COAUTHOR_OF'):

                weight_assignment_query = """MATCH (u:User)<-[:OWNED_BY]-(cb:CatalogBase)
                    WHERE u.username = "{username}" AND cb.name = "{catalog_base_name}"
                    WITH cb
                    MATCH (au1:Author)-[r:COAUTHOR_OF]-(au2:Author)
                    WHERE ((au1)<-[:AUTHORED_BY]-(:Article)-[:IN]->(cb)) AND ((au2)<-[:AUTHORED_BY]-(:Article)-[:IN]->(cb))
                    WITH au1, au2, r, cb
                    MATCH (a)-[:AUTHORED_BY]->(au1), (a)-[:AUTHORED_BY]->(au2)
                    WHERE (a)-[:IN]->(cb)
                    WITH au1, au2, r, count(a) AS weight
                    SET r.weight = weight
                    """.format(username=username, catalog_base_name=catalog_base_name)

                weight_removal_query = """MATCH (u:User)<-[:OWNED_BY]-(cb:CatalogBase)
                    WHERE u.username = "{username}" AND cb.name = "{catalog_base_name}"
                    WITH cb
                    MATCH (au1:Author)-[r:COAUTHOR_OF]-(au2:Author)
                    WHERE ((au1)<-[:AUTHORED_BY]-(:Article)-[:IN]->(cb)) AND ((au2)<-[:AUTHORED_BY]-(:Article)-[:IN]->(cb))
                    WITH au1, au2, r, cb
                    MATCH (a)-[:AUTHORED_BY]->(au1), (a)-[:AUTHORED_BY]->(au2)
                    WHERE (a)-[:IN]->(cb)
                    WITH au1, au2, r, count(a) AS weight
                    REMOVE r.weight
                    """.format(username=username, catalog_base_name=catalog_base_name)

                named_graph_query = """CALL gds.graph.project.cypher('{username}/{catalog_base_name}',
                    'MATCH (u:User)<-[:OWNED_BY]-(cb:CatalogBase)
                    WHERE u.username = "{username}" AND cb.name = "{catalog_base_name}"
                    WITH cb
                    MATCH (au:Author)
                    WHERE (au)<-[:AUTHORED_BY]-(:Article)-[:IN]->(cb)
                    RETURN id(au) AS id',
                    'MATCH (u:User)<-[:OWNED_BY]-(cb:CatalogBase)
                    WHERE u.username = "{username}" AND cb.name = "{catalog_base_name}"
                    WITH cb
                    MATCH (au1:Author)-[r:COAUTHOR_OF]-(au2:Author)
                    WHERE ((au1)<-[:AUTHORED_BY]-(:Article)-[:IN]->(cb)) AND ((au2)<-[:AUTHORED_BY]-(:Article)-[:IN]->(cb))
                    WITH au1, au2, r, cb
                    MATCH (a)-[:AUTHORED_BY]->(au1), (a)-[:AUTHORED_BY]->(au2)
                    WHERE (a)-[:IN]->(cb)
                    WITH au1, au2
                    MATCH (au1)-[r:COAUTHOR_OF]-(au2)
                    RETURN DISTINCT id(au1) AS source, id(au2) AS target, type(r) AS type, r.weight AS weight')
                """.format(username=username, catalog_base_name=catalog_base_name)

                tx.run(weight_assignment_query)
                tx.run(named_graph_query)
                tx.run(weight_removal_query)

        else:

            if graph_type == ('Article', 'CITES'):

                named_graph_query = """CALL gds.graph.project.cypher('{username}/{catalog_base_name}/{catalog_extension_name}',
                    'MATCH (u:User)<-[:OWNED_BY]-(cb:CatalogBase)<-[:EXTENDS]-(ce:CatalogExtension)
                    WHERE u.username = "{username}" AND cb.name = "{catalog_base_name}" AND ce.name = "{catalog_extension_name}"
                    WITH cb, ce
                    MATCH (a:Article)
                    WHERE (a)-[:IN]->(cb) OR (a)-[:IN]->(ce)
                    RETURN id(a) AS id',
                    'MATCH (u:User)<-[:OWNED_BY]-(cb:CatalogBase)<-[:EXTENDS]-(ce:CatalogExtension)
                    WHERE u.username = "{username}" AND cb.name = "{catalog_base_name}" AND ce.name = "{catalog_extension_name}"
                    WITH cb, ce
                    MATCH (a:Article), (c:Article)
                    WHERE ((a)-[:IN]->(cb) OR (a)-[:IN]->(ce)) AND ((c)-[:IN]->(cb) OR (c)-[:IN]->(ce))
                    WITH a, c
                    MATCH (a)-[r:CITES]-(c)
                    RETURN DISTINCT id(a) AS source, id(c) AS target, type(r) AS type')
                """.format(username=username, catalog_base_name=catalog_base_name, catalog_extension_name=catalog_extension_name)

                tx.run(named_graph_query)
            
            elif graph_type == ('Author', 'COAUTHOR_OF'):

                weight_assignment_query = """MATCH (u:User)<-[:OWNED_BY]-(cb:CatalogBase)<-[:EXTENDS]-(ce:CatalogExtension)
                    WHERE u.username = "{username}" AND cb.name = "{catalog_base_name}" AND ce.name = "{catalog_extension_name}"
                    WITH cb, ce
                    MATCH (au1:Author)-[r:COAUTHOR_OF]-(au2:Author)
                    WHERE ((au1)<-[:AUTHORED_BY]-(:Article)-[:IN]->(cb) OR (au1)<-[:AUTHORED_BY]-(:Article)-[:IN]->(ce)) AND ((au2)<-[:AUTHORED_BY]-(:Article)-[:IN]->(cb) OR (au2)<-[:AUTHORED_BY]-(:Article)-[:IN]->(ce))
                    WITH au1, au2, r, cb, ce
                    MATCH (a)-[:AUTHORED_BY]->(au1), (a)-[:AUTHORED_BY]->(au2)
                    WHERE (a)-[:IN]->(cb) OR (a)-[:IN]->(ce)
                    WITH au1, au2, r, count(a) AS weight
                    SET r.weight = weight
                    """.format(username=username, catalog_base_name=catalog_base_name, catalog_extension_name=catalog_extension_name)
                
                weight_removal_query = """MATCH (u:User)<-[:OWNED_BY]-(cb:CatalogBase)<-[:EXTENDS]-(ce:CatalogExtension)
                    WHERE u.username = "{username}" AND cb.name = "{catalog_base_name}" AND ce.name = "{catalog_extension_name}"
                    WITH cb, ce
                    MATCH (au1:Author)-[r:COAUTHOR_OF]-(au2:Author)
                    WHERE ((au1)<-[:AUTHORED_BY]-(:Article)-[:IN]->(cb) OR (au1)<-[:AUTHORED_BY]-(:Article)-[:IN]->(ce)) AND ((au2)<-[:AUTHORED_BY]-(:Article)-[:IN]->(cb) OR (au2)<-[:AUTHORED_BY]-(:Article)-[:IN]->(ce))
                    WITH r
                    REMOVE r.weight
                    """.format(username=username, catalog_base_name=catalog_base_name, catalog_extension_name=catalog_extension_name)

                named_graph_query = """CALL gds.graph.project.cypher('{username}/{catalog_base_name}/{catalog_extension_name}',
                    'MATCH (u:User)<-[:OWNED_BY]-(cb:CatalogBase)<-[:EXTENDS]-(ce:CatalogExtension)
                    WHERE u.username = "{username}" AND cb.name = "{catalog_base_name}" AND ce.name = "{catalog_extension_name}"
                    WITH cb, ce
                    MATCH (a:Article)-[:AUTHORED_BY]->(au:Author)
                    WHERE (a)-[:IN]->(cb) OR (a)-[:IN]->(ce)
                    RETURN id(au) AS id',
                    'MATCH (u:User)<-[:OWNED_BY]-(cb:CatalogBase)<-[:EXTENDS]-(ce:CatalogExtension)
                    WHERE u.username = "{username}" AND cb.name = "{catalog_base_name}" AND ce.name = "{catalog_extension_name}"
                    WITH cb, ce
                    MATCH (au1:Author), (au2:Author)
                    WHERE ((au1)<-[:AUTHORED_BY]-(:Article)-[:IN]->(cb) OR (au1)<-[:AUTHORED_BY]-(:Article)-[:IN]->(ce)) AND ((au2)<-[:AUTHORED_BY]-(:Article)-[:IN]->(cb) OR (au2)<-[:AUTHORED_BY]-(:Article)-[:IN]->(ce))
                    WITH au1, au2
                    MATCH (au1)-[r:COAUTHOR_OF]-(au2)
                    RETURN DISTINCT id(au1) AS source, id(au2) AS target, type(r) AS type, r.weight AS weight')
                """.format(username=username, catalog_base_name=catalog_base_name, catalog_extension_name=catalog_extension_name)

                tx.run(weight_assignment_query)
                tx.run(named_graph_query)
                tx.run(weight_removal_query)

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