from neo4j_client import Neo4jClient

class Neo4jAnalysisClient(Neo4jClient):

    def _named_graph_op(session, username, catalog_base_name, catalog_extension_name, graph_type):

        session.execute_write(Neo4jAnalysisClient._remove_named_graph, username, catalog_base_name, catalog_extension_name)
        session.execute_write(Neo4jAnalysisClient._create_named_graph, username, catalog_base_name, catalog_extension_name, graph_type)

    def _remove_named_graph(tx, username, catalog_base_name, catalog_extension_name):

        graph_exists_query = """CALL gds.graph.exists('{username}/{catalog_base_name}/{catalog_extension_name}') YIELD exists""".format(username=username, catalog_base_name=catalog_base_name, catalog_extension_name=catalog_extension_name)

        if tx.run(graph_exists_query).data()[0]['exists']:

            remove_graph_query = """CALL gds.graph.drop('{username}/{catalog_base_name}/{catalog_extension_name}')""".format(username=username, catalog_base_name=catalog_base_name, catalog_extension_name=catalog_extension_name)
            tx.run(remove_graph_query)

    def _create_named_graph(tx, username, catalog_base_name, catalog_extension_name, graph_type):

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
                MATCH (a:Article)
                WHERE (a)-[:IN]->(cb) OR (a)-[:IN]->(ce)
                WITH a
                MATCH (a)-[r:CITES]-(c:Article)
                RETURN id(a) AS source, id(c) AS target, type(r) AS type')
            """.format(username=username, catalog_base_name=catalog_base_name, catalog_extension_name=catalog_extension_name)
           
        elif graph_type == ('Author', 'COAUTHOR_OF'):
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
                MATCH (a:Article)-[:AUTHORED_BY]->(au:Author)
                WHERE (a)-[:IN]->(cb) OR (a)-[:IN]->(ce)
                WITH au
                MATCH (au)-[r:COAUTHOR_OF]-(m:Author)
                RETURN id(au) AS source, id(m) AS target, type(r) AS type')
            """.format(username=username, catalog_base_name=catalog_base_name, catalog_extension_name=catalog_extension_name)

        tx.run(named_graph_query)

    def calculate_betweenness_centrality(self, username, catalog_base_name, catalog_extension_name, graph_type):

        with self.driver.session() as session:
            Neo4jAnalysisClient._named_graph_op(session, username, catalog_base_name, catalog_extension_name, graph_type)
            return session.execute_read(Neo4jAnalysisClient._calculate_betweenness_centrality,  username, catalog_base_name, catalog_extension_name, graph_type)
        
    def _calculate_betweenness_centrality(tx,  username, catalog_base_name, catalog_extension_name, graph_type):

        betweenness_query = """CALL gds.betweenness.stream('{username}/{catalog_base_name}/{catalog_extension_name}') YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS betweenness_centrality_score ORDER BY score DESC""".format(username=username, catalog_base_name=catalog_base_name, catalog_extension_name=catalog_extension_name, node_type=graph_type[0])

        return tx.run(betweenness_query).data()
    
    def calculate_eigenvector_centrality(self, username, catalog_base_name, catalog_extension_name, graph_type):

        with self.driver.session() as session:
            Neo4jAnalysisClient._named_graph_op(session, username, catalog_base_name, catalog_extension_name, graph_type)
            return session.execute_read(Neo4jAnalysisClient._calculate_eigenvector_centrality,  username, catalog_base_name, catalog_extension_name, graph_type)
        
    def _calculate_eigenvector_centrality(tx,  username, catalog_base_name, catalog_extension_name, graph_type):

        eigenvector_query = """CALL gds.eigenvector.stream('{username}/{catalog_base_name}/{catalog_extension_name}') YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS eigenvector_centrality_score ORDER BY score DESC""".format(username=username, catalog_base_name=catalog_base_name, catalog_extension_name=catalog_extension_name, node_type=graph_type[0])

        return tx.run(eigenvector_query).data()
    
    def calculate_page_rank(self, username, catalog_base_name, catalog_extension_name, graph_type):

        with self.driver.session() as session:
            Neo4jAnalysisClient._named_graph_op(session, username, catalog_base_name, catalog_extension_name, graph_type)
            return session.execute_read(Neo4jAnalysisClient._calculate_page_rank,  username, catalog_base_name, catalog_extension_name, graph_type)
        
    def _calculate_page_rank(tx,  username, catalog_base_name, catalog_extension_name, graph_type):

        pagerank_query = """CALL gds.pageRank.stream('{username}/{catalog_base_name}/{catalog_extension_name}') YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS pagerank_score ORDER BY score DESC""".format(username=username, catalog_base_name=catalog_base_name, catalog_extension_name=catalog_extension_name, node_type=graph_type[0])

        return tx.run(pagerank_query).data()
    
    def calculate_degree_centrality(self, username, catalog_base_name, catalog_extension_name, graph_type):
            
        with self.driver.session() as session:
            Neo4jAnalysisClient._named_graph_op(session, username, catalog_base_name, catalog_extension_name, graph_type)
            return session.execute_read(Neo4jAnalysisClient._calculate_degree_centrality,  username, catalog_base_name, catalog_extension_name, graph_type)
        
    def _calculate_degree_centrality(tx,  username, catalog_base_name, catalog_extension_name, graph_type):

        degree_query = """CALL gds.degree.stream('{username}/{catalog_base_name}/{catalog_extension_name}') YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS degree_centrality_score ORDER BY score DESC""".format(username=username, catalog_base_name=catalog_base_name, catalog_extension_name=catalog_extension_name, node_type=graph_type[0])

        return tx.run(degree_query).data()
            
    def calculate_article_rank(self, username, catalog_base_name, catalog_extension_name, graph_type):

        with self.driver.session() as session:
            Neo4jAnalysisClient._named_graph_op(session, username, catalog_base_name, catalog_extension_name, graph_type)
            return session.execute_read(Neo4jAnalysisClient._calculate_article_rank,  username, catalog_base_name, catalog_extension_name, graph_type)
        
    def _calculate_article_rank(tx,  username, catalog_base_name, catalog_extension_name, graph_type):

        article_rank_query = """CALL gds.articleRank.stream('{username}/{catalog_base_name}/{catalog_extension_name}') YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS article_rank_score ORDER BY score DESC""".format(username=username, catalog_base_name=catalog_base_name, catalog_extension_name=catalog_extension_name, node_type=graph_type[0])

        return tx.run(article_rank_query).data()
    
    def calculate_closeness_centrality(self, username, catalog_base_name, catalog_extension_name, graph_type):

        with self.driver.session() as session:
            Neo4jAnalysisClient._named_graph_op(session, username, catalog_base_name, catalog_extension_name, graph_type)
            return session.execute_read(Neo4jAnalysisClient._calculate_closeness_centrality,  username, catalog_base_name, catalog_extension_name, graph_type)
        
    def _calculate_closeness_centrality(tx,  username, catalog_base_name, catalog_extension_name, graph_type):

        closeness_query = """CALL gds.beta.closeness.stream('{username}/{catalog_base_name}/{catalog_extension_name}') YIELD nodeId, score RETURN gds.util.asNode(nodeId) AS {node_type}, score AS closeness_centrality_score ORDER BY score DESC""".format(username=username, catalog_base_name=catalog_base_name, catalog_extension_name=catalog_extension_name, node_type=graph_type[0])

        return tx.run(closeness_query).data()
    
    def calculate_harmonic_centrality(self, username, catalog_base_name, catalog_extension_name, graph_type):

        with self.driver.session() as session:
            Neo4jAnalysisClient._named_graph_op(session, username, catalog_base_name, catalog_extension_name, graph_type)
            return session.execute_read(Neo4jAnalysisClient._calculate_harmonic_centrality,  username, catalog_base_name, catalog_extension_name, graph_type)
        
    def _calculate_harmonic_centrality(tx,  username, catalog_base_name, catalog_extension_name, graph_type):
            
            harmonic_query = """CALL gds.alpha.closeness.harmonic.stream('{username}/{catalog_base_name}/{catalog_extension_name}') YIELD nodeId, centrality RETURN gds.util.asNode(nodeId) AS {node_type}, centrality AS harmonic_centrality_score ORDER BY centrality DESC""".format(username=username, catalog_base_name=catalog_base_name, catalog_extension_name=catalog_extension_name, node_type=graph_type[0])
    
            return tx.run(harmonic_query).data()