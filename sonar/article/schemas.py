from datetime import datetime
from typing import TypedDict, List, Dict, Optional

class Article(TypedDict):
    doi: str
    # external_ids: Optional[Dict[str, str]]
    s2ag_url: Optional[str]
    title: Optional[str]
    abstract: Optional[str]
    venue: Optional[str]
    year: Optional[int]
    outbound_citation_count: Optional[int]
    inbound_citation_count: Optional[int]
    s2ag_influential_inbound_citation_count: Optional[int]
    is_open_access: Optional[bool]
    open_access_pdf_url: Optional[str]
    fields_of_study: Optional[List[str]]
    # publication_venue: Optional[Dict[str, str]]
    publication_types: Optional[List[str]]
    publication_date: Optional[datetime.date]
    # journal: Optional[Dict[str, str]]
    