from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from src.models.entities.pmc_article import PMCArticle
from src.models.entities.extras import Grant
from .base import Base

from sqlalchemy import String, Integer, TIMESTAMP, Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func



class RecordType(str, Enum):
    Article = "Article"
    Grant = "Grant"
    Repo = "Repo"
    Library = "Library"


class Source(str, Enum):
    PubMed = "PubMed"
    Europe_PMC = "Europe_PMC"
    Github = "Github"
    PYPI = "Pypi"


class Status(str, Enum):
    Pending = "Pending"
    Approved = "Approved"
    Rejected = "Rejected"


class ProductType(str, Enum):
    standard = "standard"
    implementation = "implementation"
    reference = "reference"


class Record(Base):
    """
    CHANGE: SQLAlchemy ORM model replacing the Pydantic Record/RecordRequest.
    - Uses SAEnum for enum columns, stored as VARCHAR values (native_enum=False).
    - Uses PostgreSQL ARRAY(TEXT) for 'keyword' list.
    - Adds server-side defaults for created_at/updated_at via func.now().
    """
    __tablename__ = "records" 

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    record_type: Mapped[RecordType] = mapped_column(
        SAEnum(RecordType, native_enum=False), nullable=False
    )
    source: Mapped[Source] = mapped_column(
        SAEnum(Source, native_enum=False), nullable=False
    )
    status: Mapped[Status] = mapped_column(
        SAEnum(Status, native_enum=False), nullable=False, default=Status.Pending
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

    # ---------- Relationships ----------

    article: Mapped["PMCArticle"] = relationship(
        back_populates="record",
        uselist=False,
        cascade="all, delete-orphan",
    )

    grant: Mapped[List["Grant"]] = relationship(
        cascade="all, delete-orphan",
    )