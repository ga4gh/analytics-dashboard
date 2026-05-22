from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

class PMCAuthor(BaseModel):
    id: Optional[int] = None
    fullname: str
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    initials: Optional[str] = None
    orcid: Optional[str] = None
    author_order: Optional[int] = None

    model_config = {"from_attributes": True}
    
class PMCAffiliation(BaseModel):
    id: Optional[int] = None
    author_id: int
    article_id: int
    org_name: str
    affiliation_order: int

    model_config = {"from_attributes": True}
    
class ArticleAuthor(BaseModel):
    id: Optional[int] = None
    article_id: int
    author_id: int
    author_order: int

    model_config = {"from_attributes": True}