from datetime import datetime
from typing import TypedDict, List


class Article(TypedDict):
    DOI: str
    title: str
    abstract: str
    year: int
    citation_count: int
    reference_count: int
    fields_of_study: List[str]
    publication_types: List[str]
    publication_date: str
    authors: List[str]
