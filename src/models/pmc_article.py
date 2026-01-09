from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from src.models.citation import Citation, Reference
from src.models.extras import FullText, Grant, Keyword
from src.models.pmc_author import PMCAffiliation, PMCAuthor

class PMCArticle(BaseModel):
    id: Optional[int] = None
    record_id: int

    source: str
    pm_id: Optional[str] = None
    pmc_id: str
    full_text_id: str
    doi: str
    title: str
    pub_year: int
    abstract_text: str
    affiliation: str
    publicication_status: str
    language: str
    pub_type: Optional[str] = None

    is_open_access: bool = False
    inEPMC: bool = False
    inPMC: bool = False
    hasPDF: bool = False
    hasBook: bool = False
    hasSuppl: bool = False
    cited_by_count: int = 0
    has_references: bool = False

    dateofcreation: datetime
    firstIndexdate: datetime
    fulltextreceivedate: datetime
    revisiondate: datetime
    epubdate: datetime
    firstpublicationdate: datetime

    model_config = {"from_attributes": True}
    
    
class PMCArticleFull(PMCArticle):
    authors: List[PMCAuthor] = []
    affiliations: List[PMCAffiliation] = []
    keywords: List[Keyword] = []
    grants: List[Grant] = []
    fulltexts: List[FullText] = []
    citations: List[Citation] = []
    references: List[Reference] = []