from datetime import datetime
from typing import TypedDict, List, Dict, Optional

class Article(TypedDict):
    doi: str
    s2ag_url: Optional[str]
    title: Optional[str]
    abstract: Optional[str]
    venue: Optional[str]
    year: Optional[int]
    citation_count: Optional[int]
    reference_count: Optional[int]
    outbound_citation_count: Optional[int]
    inbound_citation_count: Optional[int]
    s2ag_influential_inbound_citation_count: Optional[int]
    is_open_access: Optional[bool]
    open_access_pdf_url: Optional[str]
    fields_of_study: Optional[List[str]]
    publication_venue: Optional[str]
    publication_types: Optional[List[str]]
    publication_date: Optional[datetime.date]
    authors: Optional[List[str]]
    open_access_pdf: Optional[str]
    bibtex: Optional[str]
    