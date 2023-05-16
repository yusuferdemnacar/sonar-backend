import threading
import time

from article.schemas import Article
from author.schemas import Author
import requests
import json
import os
from multiprocessing.pool import ThreadPool
from graph.models import Citation

class S2AGService():

    def get_article(self, doi):

        #TODO: Tell the users which articles were not found in S2AG API

        article_bundle = {}

        retry_count = 0
        if doi.startswith("10.48550/arXiv."):
            doi=doi.replace("10.48550/arXiv.", "ARXIV:")
        while True:

            s2ag_article_details_url = "https://api.semanticscholar.org/graph/v1/paper/{doi}?fields=externalIds,url,title,abstract,venue,year,referenceCount,citationCount,influentialCitationCount,isOpenAccess,openAccessPdf,fieldsOfStudy,publicationVenue,publicationTypes,publicationDate,journal,authors.url,authors.name,authors.aliases,authors.affiliations,authors.homepage,authors.paperCount,authors.citationCount,authors.hIndex".format(doi=doi)
            with requests.session() as s:
                s2ag_article_details_response = s.get(s2ag_article_details_url, headers = {'x-api-key':os.environ.get('S2AG_API_KEY')})
                article_dict = {}
                
            if s2ag_article_details_response.status_code == 429:
                print("S2AG API returned status code {status_code} for DOI {doi}".format(status_code=s2ag_article_details_response.status_code, doi=doi))
                continue
                
            if s2ag_article_details_response.status_code != 200:
                return None, None
            
            print("S2AG API returned status code {status_code} for DOI {doi}".format(status_code=s2ag_article_details_response.status_code, doi=doi))

            s2ag_article_details_response_dict = json.loads(s2ag_article_details_response.text)

            if s2ag_article_details_response_dict["citationCount"] > 10000:
                inbound_citation_article_dois_query_set = Citation.objects.filter(cited_article_doi=doi).values_list("citing_article_doi", flat=True)
                inbound_citation_article_dois = list(inbound_citation_article_dois_query_set)
            else:
                inbound_citation_article_dois = self.get_inbound_citation_article_dois([doi])

            outbound_citation_articles = self.get_outbound_citation_article_dois([doi])
            rdb_outbound_citations = []

            outbound_citation_article_dois = []

            for outbound_citation_article in outbound_citation_articles:
                outbound_citation_article_dois.append(outbound_citation_article["doi"])
                if outbound_citation_article["inbound_citation_count"] > 10000:
                    rdb_outbound_citations.append(Citation(citing_article_doi=doi, cited_article_doi=outbound_citation_article["doi"]))

            article_dict["doi"] = doi
            # article_dict["external_ids"] = {}
            # for external_id_type in s2ag_article_details_response_dict["externalIds"].keys():
            #     if external_id_type != "DOI":
            #         article_dict["external_ids"][external_id_type] = s2ag_article_details_response_dict["externalIds"][external_id_type]
            article_dict["s2ag_url"] = s2ag_article_details_response_dict["url"]
            article_dict["title"] = s2ag_article_details_response_dict["title"]
            article_dict["abstract"] = s2ag_article_details_response_dict["abstract"]
            article_dict["venue"] = s2ag_article_details_response_dict["venue"]
            article_dict["year"] = s2ag_article_details_response_dict["year"]
            article_dict["outbound_citation_count"] = s2ag_article_details_response_dict["referenceCount"]
            article_dict["inbound_citation_count"] = s2ag_article_details_response_dict["citationCount"]
            article_dict["s2ag_influential_inbound_citation_count"] = s2ag_article_details_response_dict["influentialCitationCount"]
            article_dict["is_open_access"] = s2ag_article_details_response_dict["isOpenAccess"]
            if article_dict["is_open_access"]:
                article_dict["open_access_pdf_url"] = s2ag_article_details_response_dict["openAccessPdf"]["url"]
            article_dict["fields_of_study"] = s2ag_article_details_response_dict["fieldsOfStudy"]
            # article_dict["publication_venue"] = s2ag_article_details_response_dict["publicationVenue"]
            article_dict["publication_types"] = s2ag_article_details_response_dict["publicationTypes"]
            article_dict["publication_date"] = s2ag_article_details_response_dict["publicationDate"]
            # article_dict["journal"] = s2ag_article_details_response_dict["journal"]
            authors = [Author(
                name=author_dict["name"],
                s2ag_id=author_dict["authorId"],
                # external_ids={},
                s2ag_url=author_dict["url"],
                aliases=author_dict["aliases"],
                affiliations=author_dict["affiliations"],
                homepage=author_dict["homepage"],
                paper_count=author_dict["paperCount"],
                citation_count=author_dict["citationCount"],
                h_index=author_dict["hIndex"]
            ) for author_dict in s2ag_article_details_response_dict["authors"] if author_dict.get("authorId") is not None]
            article_bundle = {"article": Article(**article_dict), "authors": authors, "outbound_citation_dois": outbound_citation_article_dois, "inbound_citation_dois": inbound_citation_article_dois}

            return rdb_outbound_citations, article_bundle

    def get_articles(self, dois):

        article_bundles = []
        rdb_outbound_citations = []

        with ThreadPool(200) as pool:

            i = 0
            
            for rdb_outbound_citations, article_bundle in pool.map(self.get_article, dois):

                print("Article {i} of {n}".format(i=i, n=len(dois)))
                i += 1
                
                if article_bundle is not None:
                    article_bundles.append(article_bundle)

                if rdb_outbound_citations is not None:
                    rdb_outbound_citations += rdb_outbound_citations

        print("Number of articles: {number_of_articles}".format(number_of_articles=len(article_bundles)))

        Citation.objects.bulk_create(rdb_outbound_citations, ignore_conflicts=True)

        return article_bundles
    
    def get_inbound_citation_article_dois(self, article_dois):

        inbound_citation_article_dois = []
        inbound_citation_article_dois_lists = []

        with ThreadPool(50) as pool:
            inbound_citation_article_dois_lists = pool.map(self.get_inbound_citation_article_doi, article_dois)

        for inbound_citation_article_dois_list in inbound_citation_article_dois_lists:
            inbound_citation_article_dois += inbound_citation_article_dois_list

        return inbound_citation_article_dois

    def get_inbound_citation_article_doi(self, article_doi):

        inbound_citation_article_dois = []

        offset = 0
        limit = 1000

        next = True

        if article_doi.startswith("10.48550/arXiv."):
            article_doi=article_doi.replace("10.48550/arXiv.", "ARXIV:")
        while next:

            #print(offset, limit)
            inbound_citations_url = "https://api.semanticscholar.org/graph/v1/paper/" + article_doi + "/citations?fields=externalIds&limit=" + str(limit) + "&offset=" + str(offset)
            response = requests.get(inbound_citations_url, headers = {'x-api-key':os.environ.get('S2AG_API_KEY')})

            if response.status_code != 200:
                if response.text == "{\"error\":\"offset + limit must be < 10000\"}\n":
                    limit = 999
                continue

            s2ag_article_details_response_dict = json.loads(response.text)

            inbound_citation_article_batch = s2ag_article_details_response_dict.get('data', None)
            inbound_citation_article_batch = [inbound_citation_article.get('citingPaper', None) for inbound_citation_article in inbound_citation_article_batch]
            inbound_citation_article_externalIds_batch = [inbound_citation_article.get('externalIds', None) for inbound_citation_article in inbound_citation_article_batch]

            for inbound_citation_article_externalIds in inbound_citation_article_externalIds_batch:

                # Implement what to do if doi is not in externalIds here

                if inbound_citation_article_externalIds is None:
                    continue

                if "DOI" in inbound_citation_article_externalIds.keys():
                    inbound_citation_article_doi = inbound_citation_article_externalIds.get('DOI', None)
                else:
                    if "ArXiv" in inbound_citation_article_externalIds.keys():
                        inbound_citation_article_doi = "10.48550/arXiv." + inbound_citation_article_externalIds.get('ArXiv', None)
                    else:
                        continue

                if inbound_citation_article_doi is not None:
                    inbound_citation_article_dois.append(inbound_citation_article_doi)

            is_there_next = s2ag_article_details_response_dict.get('next', None)

            if is_there_next is not None and is_there_next != 9999:
                offset += 1000
            else:
                next = False

            #print(next)

        return inbound_citation_article_dois
    
    def get_outbound_citation_article_dois(self, article_dois):
            
        outbound_citation_article_dois = []
        outbound_citation_article_dois_lists = []

        with ThreadPool(50) as pool:
            outbound_citation_article_dois_lists = pool.map(self.get_outbound_citation_article_doi, article_dois)

        for outbound_citation_article_dois_list in outbound_citation_article_dois_lists:
            outbound_citation_article_dois += outbound_citation_article_dois_list

        return outbound_citation_article_dois
    
    def get_outbound_citation_article_doi(self, article_doi):

        outbound_citation_article_dois = []

        offset = 0
        limit = 1000

        next = True
        if article_doi.startswith("10.48550/arXiv."):
            article_doi=article_doi.replace("10.48550/arXiv.", "ARXIV:")
        while next:
            
            outbound_citations_url = "https://api.semanticscholar.org/graph/v1/paper/" + article_doi + "/references?fields=externalIds,citationCount&limit=" + str(limit) + "&offset=" + str(offset)
            response = requests.get(outbound_citations_url, headers = {'x-api-key':os.environ.get('S2AG_API_KEY')})

            if response.status_code != 200:
                if response.text == "{\"error\":\"offset + limit must be < 10000\"}\n":
                    limit = 999
                continue

            s2ag_article_details_response_dict = json.loads(response.text)

            outbound_citation_article_batch = s2ag_article_details_response_dict.get('data', None)
            outbound_citation_article_batch = [outbound_citation_article.get('citedPaper', None) for outbound_citation_article in outbound_citation_article_batch]

            for outbound_citation_article in outbound_citation_article_batch:
                    
                if outbound_citation_article is None:
                    continue

                outbound_citation_article_externalIds = outbound_citation_article.get('externalIds', None)

                if outbound_citation_article_externalIds is None:
                    continue

                # Implement what to do if doi is not in externalIds here

                if "DOI" in outbound_citation_article_externalIds.keys():
                    outbound_citation_article_doi = outbound_citation_article_externalIds.get('DOI', None)
                else:
                    if "ArXiv" in outbound_citation_article_externalIds.keys():
                        outbound_citation_article_doi = "10.48550/arXiv." + outbound_citation_article_externalIds.get('ArXiv', None)
                    else:
                        continue

                # TODO: really check if citationCount is not None

                if outbound_citation_article_doi is not None:
                    outbound_citation_article_dois.append({"doi": outbound_citation_article_doi, "inbound_citation_count": outbound_citation_article.get('citationCount', None)})

            is_there_next = s2ag_article_details_response_dict.get('next', None)

            if is_there_next is not None and is_there_next != 9999:
                offset += 1000
            else:
                next = False
                
        return outbound_citation_article_dois
    def get_multiple_articles_batch(self, article_dois, results):
        article_bundles = []

        retry_count = 0
        for doi in article_dois:
            if doi.startswith("10.48550/arXiv."):
                doi = doi.replace("10.48550/arXiv.", "ARXIV:")
        while True:

            s2ag_article_details_response = requests.post(
                    'https://api.semanticscholar.org/graph/v1/paper/batch',
                    params={'fields': 'externalIds,url,title,abstract,venue,year,referenceCount,citationCount,influentialCitationCount,isOpenAccess,openAccessPdf,fieldsOfStudy,publicationVenue,publicationTypes,publicationDate,journal,authors.url,authors.name,authors.aliases,authors.affiliations,authors.homepage,authors.paperCount,authors.citationCount,authors.hIndex'},
                    json={"ids": article_dois},
                    headers={'x-api-key': os.environ.get('S2AG_API_KEY')})

            article_dict = {}

            if s2ag_article_details_response.status_code != 200:
                status = s2ag_article_details_response.status_code
                print("S2AG API returned status code {status_code} for DOI {doi}".format(status_code=status, doi=doi))
                if retry_count < 5:
                    retry_count += 1
                    continue
                else:
                    return s2ag_article_details_response.status_code

            s2ag_article_details_response_dict = json.loads(s2ag_article_details_response.text)

            for article in s2ag_article_details_response_dict:
                if "DOI" in article["externalIds"].keys():
                    DOI = article["externalIds"]["DOI"]
                else:
                    if "ArXiv" in article["externalIds"].keys():
                        DOI = "10.48550/arXiv." + article["externalIds"]["ArXiv"]
                    else:
                        continue
                article_dict["doi"] = DOI
                # article_dict["external_ids"] = {}
                # for external_id_type in s2ag_article_details_response_dict["externalIds"].keys():
                #     if external_id_type != "DOI":
                #         article_dict["external_ids"][external_id_type] = s2ag_article_details_response_dict["externalIds"][external_id_type]
                article_dict["s2ag_url"] = article["url"]
                article_dict["title"] = article["title"]
                article_dict["abstract"] = article["abstract"]
                article_dict["venue"] = article["venue"]
                article_dict["year"] = article["year"]
                article_dict["citation_count"] = article["referenceCount"]
                article_dict["reference_count"] = article["citationCount"]
                article_dict["s2ag_influential_inbound_citation_count"] = article[
                    "influentialCitationCount"]
                article_dict["is_open_access"] = article["isOpenAccess"]
                if article_dict["is_open_access"]:
                    article_dict["open_access_pdf"] = article["openAccessPdf"]["url"]
                article_dict["fields_of_study"] = article["fieldsOfStudy"]
                # article_dict["publication_venue"] = s2ag_article_details_response_dict["publicationVenue"]
                article_dict["publication_types"] = article["publicationTypes"]
                article_dict["publication_date"] = article["publicationDate"]
                # article_dict["journal"] = s2ag_article_details_response_dict["journal"]
                article_dict["authors"] = [author_dict["name"] for author_dict in article["authors"] if author_dict.get("authorId") is not None]
                article_bundle = Article(**article_dict)
                article_bundles.append(article_bundle)

            results.extend(article_bundles)
            return
    def get_multiple_articles(self, dois):
        thread_count = int(len(dois) / 100) + 1
        print("Thread count: {thread_count}".format(thread_count=thread_count))

        threads = []
        results = []
        for i in range(thread_count):
            thread = threading.Thread(target=self.get_multiple_articles_batch, args=(dois[i * 100: (i + 1) * 100], results))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        print(results)
        return results