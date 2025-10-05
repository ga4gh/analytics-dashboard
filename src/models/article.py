from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from src.models.author import Author


class Status(str, Enum):
    PREPRINT = "Preprint"
    PUBLISHED = "Published"
    REDACTED = "Redacted"
    UPDATED = "Updated"
    UNKNOWN = "Unknown"

class Article(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    record_id: int | None = None
    title: str
    abstract: str | None = None
    journal: str
    source_id: str
    doi: str | None
    status: Status | None
    publish_date: datetime | None = None
    link: str | None = None

    # non-database field for API processing
    authors: list[Author] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str | None = None
    updated_at: datetime = Field(default_factory=datetime.now)
    updated_by: str | None = None
    deleted_at: datetime | None = None
    deleted_by: str | None = None
    version: int = 1
