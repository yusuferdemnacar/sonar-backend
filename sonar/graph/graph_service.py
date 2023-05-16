from typing import List
from article.schemas import Article
from author.schemas import Author
from catalog.schemas import CatalogBase
from neo4j_client import Neo4jClient
import time

class UserService():

    def __init__(self, neo4j_graph_client):
        self.neo4j_graph_client = neo4j_graph_client

    def create_user_node(self, username: str):
        query = """
            MERGE (u:User {username: $username})
        """
        self.neo4j_graph_client.run(query, parameters={"username": username})

class CatalogService():

    def __init__(self, neo4j_client: Neo4jClient):
        self.neo4j_client = neo4j_client

    def create_base_node(self, username: str, catalog_base_name: str):
            
        query = """
            MATCH (u:User {username: $username})
            MERGE (cb:CatalogBase {name: $catalog_base_name})-[:OWNED_BY]->(u)
        """

        self.neo4j_client.run(query, parameters={"catalog_base_name": catalog_base_name, "username": username})

    def delete_base_node(self, username: str, catalog_base_name: str):

        query = """
            MATCH (cb:CatalogBase {name: $catalog_base_name})-[:OWNED_BY]->(u:User {username: $username})
            DETACH DELETE cb
        """

        self.neo4j_client.run(query, parameters={"catalog_base_name": catalog_base_name, "username": username})

    def delete_extension_node(self, username: str, catalog_base_name: str, catalog_extension_name: str):

        query = """
            MATCH (ce:CatalogExtension {name: $catalog_extension_name})-[:EXTENDS]->(cb:CatalogBase {name: $catalog_base_name})-[:OWNED_BY]->(u:User {username: $username})
            DETACH DELETE ce
        """

        self.neo4j_client.run(query, parameters={catalog_base_name: catalog_base_name, "username": username, "catalog_extension_name": catalog_extension_name})

    def create_extension_node(self, username: str, catalog_base_name: str, catalog_extension_name: str):

        query = """
            MATCH (cb:CatalogBase {name: $catalog_base_name})-[:OWNED_BY]->(u:User {username: $username})
            MERGE (ce:CatalogExtension {name: $catalog_extension_name})-[:EXTENDS]->(cb)
        """

        self.neo4j_client.run(query, parameters={"catalog_base_name": catalog_base_name, "username": username, "catalog_extension_name": catalog_extension_name})

    def create_article_patterns(self, article_bundles):
        
        article_creation_query = """
            UNWIND $article_bundles AS article_bundle
            CALL{
                WITH article_bundle
                CREATE (a:Article {doi: article_bundle.article.doi})
                SET a.external_ids = article_bundle.article.external_ids,
                    a.s2ag_url = article_bundle.article.s2ag_url,
                    a.title = article_bundle.article.title,
                    a.abstract = article_bundle.article.abstract,
                    a.venue = article_bundle.article.venue,
                    a.year = article_bundle.article.year,
                    a.outbound_citation_count = article_bundle.article.outbound_citation_count,
                    a.inbound_citation_count = article_bundle.article.inbound_citation_count,
                    a.s2ag_influential_inbound_citation_count = article_bundle.article.s2ag_influential_inbound_citation_count,
                    a.is_open_access = article_bundle.article.is_open_access,
                    a.open_access_pdf_url = article_bundle.article.open_access_pdf_url,
                    a.fields_of_study = article_bundle.article.fields_of_study,
                    a.publication_venue = article_bundle.article.publication_venue,
                    a.publication_types = article_bundle.article.publication_types,
                    a.publication_date = article_bundle.article.publication_date,
                    a.journal = article_bundle.article.journal
                RETURN a
            }
            WITH a, article_bundle
            CALL{
                WITH a, article_bundle
                UNWIND article_bundle.outbound_citation_dois AS outbound_citation_doi
                CALL {
                    WITH a, outbound_citation_doi
                    MATCH (oc:Article)
                    WHERE oc.doi = outbound_citation_doi
                    MERGE (a)-[:CITES]->(oc)
                }
            }
            WITH a, article_bundle
            CALL{
                WITH a, article_bundle
                UNWIND article_bundle.inbound_citation_dois AS inbound_citation_doi
                CALL {
                    WITH a, inbound_citation_doi
                    MATCH (ic:Article)
                    WHERE ic.doi = inbound_citation_doi
                    MERGE (ic)-[:CITES]->(a)
                }
            }

        """

        author_creation_query = """
            UNWIND $article_bundles AS article_bundle
            MATCH (a:Article {doi: article_bundle.article.doi})
            UNWIND article_bundle.authors AS author
            MERGE (au:Author {s2ag_id: author.s2ag_id})
            ON CREATE SET
                au.name = author.name,
                au.s2ag_url = author.s2ag_url,
                au.aliases = author.aliases,
                au.affiliations = author.affiliations,
                au.homepage = author.homepage,
                au.paper_count = author.paper_count,
                au.citation_count = author.citation_count,
                au.h_index = author.h_index
            MERGE (a)-[:AUTHORED_BY]->(au)
            WITH au, article_bundle
            UNWIND article_bundle.authors AS coauthor
            MATCH (cau:Author {s2ag_id: coauthor.s2ag_id})
            WHERE cau.s2ag_id <> au.s2ag_id
            MERGE (au)-[c:COAUTHOR_OF]-(cau)
        """

        with self.neo4j_client.driver.session().begin_transaction() as tx:

            t = time.time()
            tx.run(article_creation_query, parameters={"article_bundles": article_bundles})
            print("Article creation took: ", time.time() - t)
            t = time.time()
            tx.run(author_creation_query, parameters={"article_bundles": article_bundles})
            print("Author creation took: ", time.time() - t)
            
    def create_author_node(self, author: Author):
        
        query = """
            MERGE (a:Author {s2ag_id: $author.s2ag_id})
            SET a.name = $author.name,
                a.s2ag_url = $author.s2ag_url,
                a.aliases = $author.aliases,
                a.affiliations = $author.affiliations,
                a.homepage = $author.homepage,
                a.paper_count = $author.paper_count,
                a.citation_count = $author.citation_count,
                a.h_index = $author.h_index
        """

        self.neo4j_client.run(query, parameters={"author_name": author["name"], "author": author})

    def add_articles_to_base(self, username, catalog_base_name, dois):

        query = """
            UNWIND $dois AS doi
            MATCH (a:Article), (cb:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE a.doi = doi AND cb.name = $catalog_base_name AND u.username = $username
            MERGE (a)-[i:IN]->(cb)
        """

        self.neo4j_client.run(query, parameters={"dois": dois, "catalog_base_name": catalog_base_name, "username": username})

    def add_articles_to_extension(self, username, catalog_base_name, catalog_extension_name, dois):
            
        query = """
            UNWIND $dois AS doi
            MATCH (a:Article), (ce:CatalogExtension)-[e:EXTENDS]->(cb:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE a.doi = doi AND cb.name = $catalog_base_name AND ce.name = $catalog_extension_name AND u.username = $username
            MERGE (a)-[i:IN]->(ce)
        """

        self.neo4j_client.run(query, parameters={"dois": dois, "catalog_base_name": catalog_base_name, "catalog_extension_name": catalog_extension_name, "username": username})

    def remove_article_from_base(self, username, catalog_base_name, doi):

        query = """
            MATCH (a:Article)-[i:IN]->(cb:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE a.doi = $doi AND cb.name = $catalog_base_name AND u.username = $username
            DELETE i
        """

        self.neo4j_client.run(query, parameters={"doi": doi, "catalog_base_name": catalog_base_name, "username": username})

    def remove_article_from_extension(self, username, catalog_base_name, catalog_extension_name, doi):

        query = """
            MATCH (a:Article)-[i:IN]->(ce:CatalogExtension)-[e:EXTENDS]->(cb:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE a.doi = $doi AND cb.name = $catalog_base_name AND ce.name = $catalog_extension_name AND u.username = $username
            DELETE i
        """

        self.neo4j_client.run(query, parameters={"doi": doi, "catalog_base_name": catalog_base_name, "catalog_extension_name": catalog_extension_name, "username": username})

    def get_base_articles(self, username, catalog_base_name, ) -> List[Article]:
        
        query = """
            MATCH (a:Article)-[i:IN]->(c:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE c.name = $catalog_base_name AND u.username = $username
            RETURN a AS article
        """

        result = self.neo4j_client.run(query, parameters={"catalog_base_name": catalog_base_name, "username": username})

        articles = [Article(**record["article"]) for record in result]

        return articles

    def get_base_articles_with_pagination(self, username, catalog_base_name, offset, limit) -> List[Article]:

        query = """
            MATCH (a:Article)-[i:IN]->(c:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE c.name = $catalog_base_name AND u.username = $username
            WITH a
            MATCH (a)-[o: AUTHORED_BY]->(au:Author)
            RETURN a AS article, collect(au) AS authors
            ORDER BY a.doi
            SKIP $offset
            LIMIT $limit
        """

        result = self.neo4j_client.run(query, parameters={"catalog_base_name": catalog_base_name, "username": username, "offset": offset, "limit": limit})

        articles = [{'doi': record['article']['doi'],
                     'title': record['article'].get('title', None),
                     'abstract': record['article'].get('abstract', None),
                     'year': record['article'].get('year', None),
                     'citation_count': record['article'].get('inbound_citation_count', None),
                     'reference_count': record['article'].get('outbound_citation_count', None),
                     'fields_of_study': record['article'].get('fields_of_study', None),
                     'publication_types': record['article'].get('publication_types', None),
                     'publication_date': record['article'].get('publication_date', None,),
                     'authors': [{'author_id': author['s2ag_id'], 'author_name': author['name']} for author in
                                 record['authors']]
                     } for record in result]

        return articles

    def get_base_articles_count(self, username, catalog_base_name) -> int:

        query = """
            MATCH (a:Article)-[i:IN]->(c:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE c.name = $catalog_base_name AND u.username = $username
            RETURN count(a) AS article_count
        """

        result = self.neo4j_client.run(query, parameters={"catalog_base_name": catalog_base_name, "username": username})
        count = int(result[0]["article_count"])

        return count
    
    def get_extension_articles(self, username, catalog_base_name, extension_name) -> List[Article]:

        query = """
            MATCH (a:Article)-[i:IN]->(c:CatalogExtension)-[e:EXTENDS]->(cb:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE cb.name = $catalog_base_name AND u.username = $username AND c.name = $extension_name
            WITH a
            MATCH (a)-[o: AUTHORED_BY]->(au:Author)
            RETURN a AS article, collect(au) AS authors
        """

        result = self.neo4j_client.run(query, parameters={"catalog_base_name": catalog_base_name, "username": username, "extension_name": extension_name})

        articles = [{'doi': record['article']['doi'],
                     'title': record['article'].get('title', None),
                     'abstract': record['article'].get('abstract', None),
                     'year': record['article'].get('year', None),
                     'citation_count': record['article'].get('inbound_citation_count', None),
                     'reference_count': record['article'].get('outbound_citation_count', None),
                     'fields_of_study': record['article'].get('fields_of_study', None),
                     'publication_types': record['article'].get('publication_types', None),
                     'publication_date': record['article'].get('publication_date', None,),
                     'authors': [{'author_id': author['s2ag_id'], 'author_name': author['name']} for author in
                                 record['authors']]
                     } for record in result]

        return articles

    def get_extension_articles_with_pagination(self, username, catalog_base_name, extension_name, offset, limit) -> List[Article]:


        query = """
            MATCH (a:Article)-[i:IN]->(c:CatalogExtension)-[e:EXTENDS]->(cb:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE cb.name = $catalog_base_name AND u.username = $username AND c.name = $extension_name
            WITH a
            MATCH (a)-[o: AUTHORED_BY]->(au:Author)
            RETURN a AS article, collect(au) AS authors
            ORDER BY a.doi
            SKIP $offset
            LIMIT $limit
        """

        result = self.neo4j_client.run(query, parameters={"catalog_base_name": catalog_base_name,"extension_name":extension_name ,"username": username, "offset": offset, "limit": limit})

        articles = [{'doi': record['article']['doi'],
                     'title': record['article'].get('title', None),
                     'abstract': record['article'].get('abstract', ''),
                     'year': record['article'].get('year', None),
                     'citation_count': record['article'].get('inbound_citation_count', None),
                     'reference_count': record['article'].get('outbound_citation_count', None),
                     'fields_of_study': record['article'].get('fields_of_study', []),
                     'publication_types': record['article'].get('publication_types', []),
                     'publication_date': record['article'].get('publication_date', None,),
                     'authors': [{'author_id': author['s2ag_id'], 'author_name': author['name']} for author in
                                 record['authors']]
                     } for record in result]


        return articles

    def get_extension_articles_count(self, username, catalog_base_name, extension_name) -> int:

        query = """
            MATCH (a:Article)-[i:IN]->(c:CatalogExtension)-[e:EXTENDS]->(cb:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE cb.name = $catalog_base_name AND u.username = $username AND c.name = $extension_name
            RETURN count(a) AS article_count
        """

        result = self.neo4j_client.run(query, parameters={"catalog_base_name": catalog_base_name, "extension_name": extension_name,"username": username})

        count = int(result["article_count"])

        return count


    def check_if_article_in_base(self, username, catalog_base_name, doi) -> bool:
        
        query = """
            MATCH (a:Article)-[i:IN]->(c:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE c.name = $catalog_base_name AND u.username = $username AND a.doi = $doi
            RETURN a AS Article
        """.format(catalog_base_name=catalog_base_name, username=username, doi=doi)

        result = self.neo4j_client.run(query, parameters={"catalog_base_name": catalog_base_name, "username": username, "doi": doi})

        if len(result) > 0:
            return True
        else:
            return False
        
    def check_if_article_in_extension(self, username, catalog_base_name, extension_name, doi) -> bool:

        query = """
            MATCH (a:Article)-[i:IN]->(c:CatalogExtension)-[e:EXTENDS]->(cb:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE cb.name = $catalog_base_name AND u.username = $username AND c.name = $extension_name AND a.doi = $doi
            RETURN a AS Article
        """.format(catalog_base_name=catalog_base_name, username=username, doi=doi)

        result = self.neo4j_client.run(query, parameters={"catalog_base_name": catalog_base_name, "username": username, "extension_name": extension_name, "doi": doi})

        if len(result) > 0:
            return True
        else:
            return False

    def check_if_base_exists(self, username, catalog_base_name) -> bool:
        
        query = """
            MATCH (c:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE c.name = $catalog_base_name AND u.username = $username
            RETURN c AS CatalogBase
        """

        result = self.neo4j_client.run(query, parameters={"catalog_base_name": catalog_base_name, "username": username})

        if len(result) != 0:
            return True
        else:
            return False
        
    def check_if_extension_exists(self, username, base_name, extension_name) -> bool:
        
        query = """
            MATCH (ce:CatalogExtension)-[e:EXTENDS]->(cb:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE ce.name = $extension_name AND cb.name = $base_name AND u.username = $username
            RETURN e AS CatalogExtension
        """

        result = self.neo4j_client.run(query, parameters={"extension_name": extension_name, "base_name": base_name, "username": username})

        if len(result) != 0:
            return True
        else:
            return False
        
    def get_existing_articles(self, dois) -> List[Article]:
        
        query = """
            MATCH (a:Article)
            WHERE a.doi IN $doi_list
            RETURN a AS article
        """

        result = self.neo4j_client.run(query, parameters={"doi_list": list(dois)})

        articles = [Article(**record["article"]) for record in result]

        return articles

    def get_existing_article_with_doi(self, doi):

        query = """
            MATCH (a:Article)
            WHERE a.doi = $doi
            WITH a
            OPTIONAL MATCH (a)-[o: AUTHORED_BY]->(au:Author)
            RETURN a AS article, collect(au) AS authors
        """

        result = self.neo4j_client.run(query, parameters={"doi": doi})

        article =[{'doi': record['article']['doi'],
                     'title': record['article'].get('title', None),
                     'abstract': record['article'].get('abstract', ''),
                     'year': record['article'].get('year', None),
                     'citation_count': record['article'].get('inbound_citation_count', None),
                     'reference_count': record['article'].get('outbound_citation_count', None),
                     'fields_of_study': record['article'].get('fields_of_study', []),
                     'publication_types': record['article'].get('publication_types', []),
                     'publication_date': record['article'].get('publication_date', None,),
                     'authors': [{'author_id': author['s2ag_id'], 'author_name': author['name']} for author in
                                 record['authors']]
                     } for record in result]

        return article
    
    def get_existing_authors(self, author_name_list) -> bool:

        query = """
            MATCH (a:Author)
            WHERE a.name IN $author_name_list
            RETURN a AS author
        """

        result = self.neo4j_client.run(query, parameters={"author_name_list": author_name_list})

        authors = [Author(**record["author"]) for record in result]

        return authors

    def get_all_catalog_bases_of_user(self, username) -> List[CatalogBase]:

        query = """
            MATCH(c:CatalogBase) - [o: OWNED_BY]->(u:User)
            WHERE u.username = $username
            OPTIONAL MATCH (a:Article) - [i:IN] -> (c)
            RETURN c.name AS catalog_base, count(a) as article_count
        """


        result = self.neo4j_client.run(query, parameters={"username": username})

        catalog_bases = [{"catalog_base_name": record['catalog_base'], "article_count": int(record['article_count'])} for record in result]

        return catalog_bases

    def get_extensions_of_catalog_base(self, username, catalog_base_name) -> List[str]:

        query = """
            MATCH (c:CatalogExtension)-[e:EXTENDS]->(cb:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE cb.name = $catalog_base_name AND u.username = $username
            RETURN collect(c.name) AS catalog_extensions
        """

        result = self.neo4j_client.run(query, parameters={"catalog_base_name": catalog_base_name, "username": username})

        catalog_extensions = result[0]["catalog_extensions"]

        return catalog_extensions