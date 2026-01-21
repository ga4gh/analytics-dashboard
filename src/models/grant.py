from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class Grant(BaseModel):
    id: Optional[int] = None,
    record_id: str
    grant_id: Optional[str] = None
    agency: str
    family_name: str
    given_name: str
    orcid: str
    funder_name: str
    grant: str
    doi: str
    title: str
    start_date: datetime
    end_date: datetime
    institution_name: str

    model_config = {"from_attributes": True}