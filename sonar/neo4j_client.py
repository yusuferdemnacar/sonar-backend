from neo4j import GraphDatabase

class Neo4jClient:

    def __init__(self):
        self.driver = GraphDatabase.driver(uri='bolt://localhost:7687', auth=('neo4j','a1b2c3d4'))

    def close(self):
        self.driver.close()

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



    @staticmethod
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

    @staticmethod
    def _create_author(tx, authorId, name):
        tx.run("CREATE (a:Author {name: $name, authorId: $authorId})", name=name, authorId=authorId)

    @staticmethod
    def _create_author_of(tx, authorId, paperId):
        tx.run(
            "MATCH (a:Author),(p:Article) WHERE a.authorId = $authorId AND p.paperId = $paperId CREATE (a)-[:AUTHOR_OF]->(p)",
            authorId=authorId, paperId=paperId)

    @staticmethod
    def _create_citation(tx, citer, cited):
        tx.run(
            "MATCH (a:Article),(p:Article) WHERE a.DOI = $citer AND p.DOI = $cited CREATE (a)-[:CITES]->(p)",
            citer=citer, cited=cited)
