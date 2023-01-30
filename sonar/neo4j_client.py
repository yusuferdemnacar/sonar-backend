from neo4j import GraphDatabase

class Neo4jClient:

    def __init__(self):
        self.driver = GraphDatabase.driver(uri='neo4j+s://3a7e0e08.databases.neo4j.io', auth=('neo4j','4Lxnu_rI96rB5nqU9a4q6UNawRfo6RRwdrkW-HsozT0'))

    def close(self):
        self.driver.close()