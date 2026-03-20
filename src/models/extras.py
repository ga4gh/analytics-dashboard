from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

class Keyword(BaseModel):
    id: Optional[int] = None
    article_id: int
    value: List[str]

    model_config = {"from_attributes": True}
    
class FullText(BaseModel):
    id: Optional[int] = None
    article_id: int
    availability: str
    availability_code: str
    document_style: str
    site: str
    url: str

    model_config = {"from_attributes": True}