from neo4j import GraphDatabase
from os import environ

class Neo4jClient:

    def __init__(self):
        print(environ.get('NEO4J_HOST'))
        self.driver = GraphDatabase.driver(uri=environ.get('NEO4J_HOST'), auth=(environ.get('NEO4J_USER'),environ.get('NEO4J_PASSWORD')))

    def close(self):
        self.driver.close()