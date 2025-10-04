from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

class Affiliation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    author_id: int 
    institute: str
    location: str | None = None
    
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str | None = None
    updated_at: datetime = Field(default_factory=datetime.now)
    updated_by: str | None = None
    deleted_at: datetime | None = None
    deleted_by: str | None = None
    version: int = 1 
