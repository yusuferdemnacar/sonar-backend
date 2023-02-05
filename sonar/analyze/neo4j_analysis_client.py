from neo4j_client import Neo4jClient

class Neo4jAnalysisClient(Neo4jClient):

    def _remove_named_graph(tx, username):

        graph_exists_query = """CALL gds.graph.exists('{username}') YIELD exists""".format(username=username)

        if tx.run(graph_exists_query).data()[0]['exists']:

            remove_graph_query = """CALL gds.graph.drop('{username}')""".format(username=username)
            tx.run(remove_graph_query)

    def _create_named_graph(tx, username, node_type, edge_type):

        named_graph_query = """CALL gds.graph.project.cypher('{username}', 'MATCH (n:{node_type}) WHERE n.owner = "{username}" RETURN id(n) AS id', 'MATCH (n:{node_type}) WHERE n.owner = "{username}" MATCH (n)-[r:{edge_type}]->(m) RETURN id(n) AS source, id(m) AS target, type(r) AS type')""".format(username=username, node_type=node_type, edge_type=edge_type)

        tx.run(named_graph_query)

    def calculate_betweenness(self, username, node_type, edge_type):

        with self.driver.session() as session:
            session.run(Neo4jAnalysisClient._remove_named_graph, username)
            session.run(Neo4jAnalysisClient._create_named_graph, username, node_type, edge_type)
            return session.execute_read(Neo4jAnalysisClient._calculate_betweenness, username, node_type, edge_type)
        
    def _calculate_betweenness(tx, username, node_type):

        betweenness_query = """CALL gds.betweenness.stream('{username}') YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS betweenness_centrality_score ORDER BY score DESC""".format(username=username, node_type=node_type)

        return tx.run(betweenness_query).data()
    
    def calculate_eigenvector(self, username, node_type, edge_type):

        with self.driver.session() as session:
            session.run(Neo4jAnalysisClient._remove_named_graph, username)
            session.run(Neo4jAnalysisClient._create_named_graph, username, node_type, edge_type)
            return session.run(Neo4jAnalysisClient._calculate_eigenvector, username, node_type, edge_type)
        
    def _calculate_eigenvector(tx, username, node_type):

        eigenvector_query = """CALL gds.eigenvector.stream('{username}') YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS eigenvector_centrality_score ORDER BY score DESC""".format(username=username, node_type=node_type)

        return tx.run(eigenvector_query).data()
    
    def calculate_pagerank(self, username, node_type, edge_type):

        with self.driver.session() as session:
            session.run(Neo4jAnalysisClient._remove_named_graph, username)
            session.run(Neo4jAnalysisClient._create_named_graph, username, node_type, edge_type)
            return session.run(Neo4jAnalysisClient._calculate_pagerank, username, node_type, edge_type)
        
    def _calculate_pagerank(tx, username, node_type):

        pagerank_query = """CALL gds.pageRank.stream('{username}') YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS pagerank_score ORDER BY score DESC""".format(username=username, node_type=node_type)

        return tx.run(pagerank_query).data()
    
    def calculate_degree_centrality(self, username, node_type, edge_type):
            
            with self.driver.session() as session:
                session.run(Neo4jAnalysisClient._remove_named_graph, username)
                session.run(Neo4jAnalysisClient._create_named_graph, username, node_type, edge_type)
                return session.run(Neo4jAnalysisClient._calculate_degree, username, node_type, edge_type)
            
    def _calculate_degree_centrality(tx, username, node_type):

        degree_query = """CALL gds.degree.stream('{username}') YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS degree_centrality_score ORDER BY score DESC""".format(username=username, node_type=node_type)

        return tx.run(degree_query).data()
    
    def calculate_closeness_centrality(self, username, node_type, edge_type):

        with self.driver.session() as session:
            session.run(Neo4jAnalysisClient._remove_named_graph, username)
            session.run(Neo4jAnalysisClient._create_named_graph, username, node_type, edge_type)
            return session.run(Neo4jAnalysisClient._calculate_closeness, username, node_type, edge_type)
        
    def _calculate_closeness_centrality(tx, username, node_type):

        closeness_query = """CALL gds.closeness.stream('{username}') YIELD nodeId, centrality RETURN gds.util.asNode(nodeId) AS {node_type}, centrality AS closeness_centrality_score ORDER BY centrality DESC""".format(username=username, node_type=node_type)

        return tx.run(closeness_query).data()