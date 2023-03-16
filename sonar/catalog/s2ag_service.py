from article.schemas import Article
from author.schemas import Author
import requests
import json

class S2AGService():

    def get_article(self, doi):

        s2ag_article_details_url = "https://api.semanticscholar.org/graph/v1/paper/{doi}?fields=externalIds,url,title,abstract,venue,year,referenceCount,citationCount,influentialCitationCount,isOpenAccess,openAccessPdf,fieldsOfStudy,publicationVenue,publicationTypes,publicationDate,journal,authors.url,authors.name,authors.aliases,authors.affiliations,authors.homepage,authors.paperCount,authors.citationCount,authors.hIndex,citations.externalIds,references.externalIds".format(doi=doi)
        response = requests.get(s2ag_article_details_url)
        article_dict = {}
        if response.status_code != 200:
            return response.status_code

        response_dict = json.loads(response.text)
        article_dict["doi"] = doi
        # article_dict["external_ids"] = {}
        # for external_id_type in response_dict["externalIds"].keys():
        #     if external_id_type != "DOI":
        #         article_dict["external_ids"][external_id_type] = response_dict["externalIds"][external_id_type]
        article_dict["s2ag_url"] = response_dict["url"]
        article_dict["title"] = response_dict["title"]
        article_dict["abstract"] = response_dict["abstract"]
        article_dict["venue"] = response_dict["venue"]
        article_dict["year"] = response_dict["year"]
        article_dict["outbound_citation_count"] = response_dict["referenceCount"]
        article_dict["inbound_citation_count"] = response_dict["citationCount"]
        article_dict["s2ag_influential_inbound_citation_count"] = response_dict["influentialCitationCount"]
        article_dict["is_open_access"] = response_dict["isOpenAccess"]
        if article_dict["is_open_access"]:
            article_dict["open_access_pdf_url"] = response_dict["openAccessPdf"]["url"]
        article_dict["fields_of_study"] = response_dict["fieldsOfStudy"]
        # article_dict["publication_venue"] = response_dict["publicationVenue"]
        article_dict["publication_types"] = response_dict["publicationTypes"]
        article_dict["publication_date"] = response_dict["publicationDate"]
        # article_dict["journal"] = response_dict["journal"]
        authors = [Author(**author_dict) for author_dict in response_dict["authors"]]
        inbound_citation_dois = [citation["externalIds"]["DOI"] for citation in response_dict["citations"] if (citation.get("paperId") is not None and citation.get("externalIds") is not None and "DOI" in citation["externalIds"].keys())]
        outbound_citation_dois = [reference["externalIds"]["DOI"] for reference in response_dict["references"] if (reference.get("paperId") is not None and reference.get("externalIds") is not None and "DOI" in reference["externalIds"].keys())]

        return {"article": Article(**article_dict), "authors": authors, "inbound_citation_dois": inbound_citation_dois, "outbound_citation_dois": outbound_citation_dois}
    