from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

class RecordType(str, Enum):
    ARTICLE = "Article"
    GRANT = "Grant"
    REPO = "Repo"
    LIBRARY = "Library"

class Source(str, Enum):
    PUBMED = "PubMed"
    EUROPE_PMC = "Europe PMC"
    GITHUB = "Github"
    PYPI = "Pypi"

class Status(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class ProductType(str, Enum):
    STANDARD = "standard"
    IMPLEMENTATION = "implementation"
    REFERENCE = "reference"

class Record(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None

    record_type: RecordType
    source: Source
    status: Status = Status.PENDING
    keyword: list[str]
    product_line: ProductType | None = None

    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str
    updated_at: datetime = Field(default_factory=datetime.now)
    updated_by: str
    deleted_at: datetime | None = None
    deleted_by: str | None = None
    version: int = 1
