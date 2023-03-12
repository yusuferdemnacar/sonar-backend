from typing import TypedDict


class Neo4jUser(TypedDict):
    username: str
    first_name: str
    last_name: str
    email: str

