from neo4j import GraphDatabase
from article.serializers import ArticleSerializer
from author.serializers import AuthorSerializer
import os 

class Neo4jClient:

    def __init__(self):
        self.driver = GraphDatabase.driver(uri=os.environ.get("GRAPH_DB_URI"), auth=(os.environ.get("GRAPH_DB_USER"),os.environ.get("GRAPH_DB_PASSWORD")))

    def close(self):
        self.driver.close()

    def create_article_nodes_batch(self, article_set):

        article_list = []

        for article in article_set:
            
            article_list.append(dict(ArticleSerializer(article).data))

        with self.driver.session() as session:
            session.execute_write(Neo4jClient._create_article_nodes_batch, article_list)

    def create_author_nodes_batch(self, author_set):

        author_list = []

        for author in author_set:
            author_list.append(dict(AuthorSerializer(author).data))

        with self.driver.session() as session:
            session.execute_write(Neo4jClient._create_author_nodes_batch, author_list)

    def create_citation_edges_batch(self, citation_set, batch_size=500):

        citation_list = []

        for citation in citation_set:
            citation_list.append({"citer": citation[0], "citee": citation[1], "type": "cites"})

        batches = [citation_list[x:x+batch_size] for x in range(0, len(citation_list), batch_size)]

        with self.driver.session() as session:
            i = 0
            for batch in batches:
                i += 1
                print("Citation batch " + str(i) + " of " + str(len(batches)))
                session.execute_write(Neo4jClient._create_citation_edges_batch, batch)

    def create_authorship_edges_batch(self, authorship_set, batch_size=500):

        authorship_list = []

        for authorship in authorship_set:
            authorship_list.append({"author": authorship[0], "article": authorship[1], "type": "authored"})

        batches = [authorship_list[x:x+batch_size] for x in range(0, len(authorship_list), batch_size)]

        with self.driver.session() as session:
            i = 0
            for batch in batches:
                i += 1
                print("Authorship batch " + str(i) + " of " + str(len(batches)))
                session.execute_write(Neo4jClient._create_authorship_edges_batch, batch)

    def create_articles(self, article_list):
        with self.driver.session() as session:
            for article in article_list:
                session.execute_write(
                    self._create_article,
                    article.DOI,
                    article.title,
                    article.abstract,
                    article.year,
                    article.citation_count,
                    article.reference_count,
                    article.fields_of_study,
                    article.publication_types,
                    article.publication_date,
                    article.authors
                )

    def create_relations(self, edges):
        with self.driver.session() as session:
            for tuple in edges:
                session.execute_write(
                    self._create_citation,
                    tuple[0],
                    tuple[1]
                )

    def _create_article_nodes_batch(tx, article_list):

        tx.run("""
            WITH $batch AS batch
            UNWIND batch AS article
            CREATE (p:Article)
            SET p += article;
        """, batch=article_list)

    def _create_author_nodes_batch(tx, author_list):

        tx.run("""
            WITH $batch AS batch
            UNWIND batch AS author
            CREATE (p:Author)
            SET p += author;
        """, batch=author_list)

    def _create_citation_edges_batch(tx, citation_list):

        citation_entities = []

        for citation in citation_list:
            citation_entities.append({"citer": citation["citer"], "citee": citation["citee"], "type": "cites"})

        tx.run("""
            WITH $batch AS batch
            UNWIND batch AS citation
            MATCH (citer) WHERE citer.DOI = citation.citer
            MATCH (citee) WHERE citee.DOI = citation.citee
            CREATE (citer)-[:Cites]->(citee)
        """, batch=citation_entities)

    def _create_authorship_edges_batch(tx, authorship_list):

        authorship_entities = []

        for authorship in authorship_list:
            authorship_entities.append({"author": authorship["author"], "article": authorship["article"], "type": "author_of"})

        tx.run("""
            WITH $batch AS batch
            UNWIND batch AS authorship
            MATCH (author) WHERE author.name = authorship.author
            MATCH (article) WHERE article.DOI = authorship.article
            CREATE (author)-[:Author_of]->(article)
        """, batch=authorship_entities)

    def _create_article(tx,
                        DOI,
                        title,
                        abstract,
                        year,
                        citation_count,
                        reference_count,
                        fields_of_study,
                        publication_types,
                        publication_date,
                        authors):
        tx.run("CREATE (p:Article {DOI: $DOI,title: $title, abstract: $abstract,year: $year,citation_count: $citation_count,reference_count: $reference_count,fields_of_study: $fields_of_study,publication_types: $publication_types,publication_date: $publication_date, authors:$authors})",
               DOI=DOI,
               title=title,
               abstract=abstract,
               year=year,
               citation_count=citation_count,
               reference_count=reference_count,
               fields_of_study=fields_of_study,
               publication_types=publication_types,
               publication_date=publication_date,
               authors=authors)

    def _create_author(tx, authorId, name):
        tx.run("CREATE (a:Author {name: $name, authorId: $authorId})", name=name, authorId=authorId)

    def _create_author_of(tx, authorId, paperId):
        tx.run(
            "MATCH (a:Author),(p:Article) WHERE a.authorId = $authorId AND p.paperId = $paperId CREATE (a)-[:AUTHOR_OF]->(p)",
            authorId=authorId, paperId=paperId)

    def _create_citation(tx, citer, cited):
        tx.run(
            "MATCH (a:Article),(p:Article) WHERE a.DOI = $citer AND p.DOI = $cited CREATE (a)-[:CITES]->(p)",
            citer=citer, cited=cited)
