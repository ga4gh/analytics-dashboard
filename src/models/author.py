from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field
from src.models.affiliation import Affiliation

class ArticleType(str, Enum):
    ARTICLE = 'Article'
    GRANT = 'Grant'

class Author(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    article_id: int 
    name: str
    contact: str | None = None
    is_primary: bool
    article_type: ArticleType

    #non-database field for API processing
    affiliations: List[Affiliation] = Field(default_factory=list, exclude=True)
    
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str | None = None
    updated_at: datetime = Field(default_factory=datetime.now)
    updated_by: str | None = None
    deleted_at: datetime | None = None
    deleted_by: str | None = None
    version: int = 1 
