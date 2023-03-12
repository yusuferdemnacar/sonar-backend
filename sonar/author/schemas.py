from typing import List, TypedDict


class Author(TypedDict):
    name: str
    paper_count: int
    citation_count: int
    h_index: int
    affiliations: List[str]
