from typing import List

class UserService():

    def __init__(self, neo4j_graph_client):
        self.neo4j_graph_client = neo4j_graph_client

    def create_user_node(self, username: str):
        query = """
            MERGE (u:User {username: $username})
        """
        self.neo4j_graph_client.run(query, parameters={"username": username})