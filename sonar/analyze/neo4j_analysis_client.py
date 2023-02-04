from neo4j_client import Neo4jClient


class Neo4jAnalysisClient(Neo4jClient):

    def calculate_betweenness(self, username, node_type, edge_type):

        with self.driver.session() as session:
            return session.execute_read(Neo4jAnalysisClient._calculate_betweenness, username, node_type, edge_type)
        
    def _calculate_betweenness(tx, username, node_type, edge_type):

        graph_exists_query = """CALL gds.graph.exists('graph') YIELD exists"""

        if tx.run(graph_exists_query).data()[0]['exists']:

            remove_graph_query = """CALL gds.graph.drop('graph')"""
            tx.run(remove_graph_query)

        named_graph_query = """CALL gds.graph.project('graph', '{node_type}', '{edge_type}')""".format(
            username=username, node_type=node_type, edge_type=edge_type)

        betweenness_query = """CALL gds.betweenness.stream('graph') YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS Article, score AS betweenness_centrality_score ORDER BY score DESC"""

        tx.run(named_graph_query)
        return tx.run(betweenness_query).data()