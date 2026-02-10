from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import String, Integer, TIMESTAMP, Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


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


class Record(Base):
    """
    CHANGE: SQLAlchemy ORM model replacing the Pydantic Record/RecordRequest.
    - Uses SAEnum for enum columns, stored as VARCHAR values (native_enum=False).
    - Uses PostgreSQL ARRAY(TEXT) for 'keyword' list.
    - Adds server-side defaults for created_at/updated_at via func.now().
    """
    __tablename__ = "record" 

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    record_type: Mapped[RecordType] = mapped_column(
        SAEnum(RecordType, native_enum=False), nullable=False
    )
    source: Mapped[Source] = mapped_column(
        SAEnum(Source, native_enum=False), nullable=False
    )
    status: Mapped[Status] = mapped_column(
        SAEnum(Status, native_enum=False), nullable=False, default=Status.PENDING
    )


    keyword: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)

    product_line: Mapped[Optional[ProductType]] = mapped_column(
        SAEnum(ProductType, native_enum=False), nullable=True
    )


    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    updated_by: Mapped[str] = mapped_column(String(64), nullable=False)

    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)