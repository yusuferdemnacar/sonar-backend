from typing import TypedDict, List

from django.db import models
from django.contrib.auth.models import User

from article.schemas import Article


class CatalogBase(TypedDict):
    owner_id: int
    catalog_name: str
    articles: List[Article]

class CatalogExtension(TypedDict):
    catalog_extension_name: str
    catalog_base_name: str

