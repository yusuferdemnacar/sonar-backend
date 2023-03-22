from typing import List, TypedDict, Optional, Dict

class Author(TypedDict):
    name: Optional[str]
    s2ag_id: Optional[str]
    # external_ids: Optional[Dict[str, str]]
    s2ag_url: Optional[str]
    aliases: Optional[List[str]]
    affiliations: Optional[List[str]]
    homepage: Optional[str]
    paper_count: Optional[int]
    citation_count: Optional[int]
    h_index: Optional[int]
