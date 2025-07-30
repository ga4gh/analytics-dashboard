from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class Animal(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int
    species: str
    breed: str
    owner: Optional[str] = None
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    version: int

class AnimalRequest(BaseModel):
    name: str
    age: int
    species: str
    breed: str
    owner: Optional[str] = None
