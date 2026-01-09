from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

class Citation(BaseModel):
    id: Optional[int] = None
    article_id: int
    citation_id: str
    source: str
    citation_type: str
    title: str
    authors: str
    pub_year: int
    citation_count: int

    model_config = {"from_attributes": True}
    
class Reference(BaseModel):
    id: Optional[int] = None
    article_id: int
    reference_id: str
    source: str
    citation_type: str
    title: str
    authors: str
    pub_year: int
    ISSN: Optional[str] = None
    ESSN: Optional[str] = None
    cited_order: int
    match: bool

    model_config = {"from_attributes": True}