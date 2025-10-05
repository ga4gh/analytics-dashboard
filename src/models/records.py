from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class Record(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    record_type: str
    source: str
    status: str
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime
    deleted_by: Optional[str]
    deleted_at: Optional[datetime]
    version: int