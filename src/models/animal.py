from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Animal(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int
    species: str
    breed: str
    owner: str | None = None
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    deleted_at: datetime | None = None
    deleted_by: str | None = None
    version: int

class AnimalRequest(BaseModel):
    name: str
    age: int
    species: str
    breed: str
    owner: str | None = None
