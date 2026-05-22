from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

class Citation(BaseModel):
    id: Optional[int] = None
    article_id: int
    citation_id: str
    source: Optional[str] = None
    citation_type: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[str] = None
    pub_year: Optional[int] = None
    citation_count: int

    model_config = {"from_attributes": True}
    
class Reference(BaseModel):
    id: Optional[int] = None
    article_id: int
    reference_id: str
    source: Optional[str] = None
    citation_type: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[str] = None
    pub_year: Optional[int] = None
    ISSN: Optional[str] = None
    ESSN: Optional[str] = None
    cited_order: int
    match: bool

    model_config = {"from_attributes": True}
    
class CitationList(BaseModel):
    citations: list[Citation]
    citation_count: int
    
class CitationOverYears(BaseModel):
    pub_year: int
    year_count: int
    commulative_count: int

class TotalCitations(BaseModel):
    total_citations: int
    citations_over_years: list[CitationOverYears]