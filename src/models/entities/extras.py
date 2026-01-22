from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Keyword(Base):
    __tablename__ = "pmc_keywords"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("pmc_articles.id", ondelete="CASCADE"), nullable=False)
    value: Mapped[List[str]] = mapped_column(ARRAY(String))  # PostgreSQL array

    # Audit fields
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    deleted_by: Mapped[Optional[str]] = mapped_column(String(64))
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)


class Grant(Base):
    __tablename__ = "grants"

    # ---------- PK / FK ----------
    id: Mapped[int] = mapped_column(primary_key=True)
    record_id: Mapped[int] = mapped_column(
        ForeignKey("record.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ---------- Core grant fields ----------
    grant_id: Mapped[Optional[str]] = mapped_column(String(128))
    agency: Mapped[Optional[str]] = mapped_column(Text)

    family_name: Mapped[Optional[str]] = mapped_column(Text)
    given_name: Mapped[Optional[str]] = mapped_column(Text)
    orcid: Mapped[Optional[str]] = mapped_column(Text)

    funder_name: Mapped[Optional[str]] = mapped_column(Text)
    doi: Mapped[Optional[str]] = mapped_column(Text)
    title: Mapped[Optional[str]] = mapped_column(Text)

    start_date: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True)
    )
    end_date: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True)
    )

    institution_name: Mapped[Optional[str]] = mapped_column(Text)

    # ---------- Audit ----------
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )
    deleted_by: Mapped[Optional[str]] = mapped_column(String(64))
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True)
    )

    version: Mapped[int] = mapped_column(Integer, default=1)


class FullText(Base):
    __tablename__ = "fulltexts"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("pmc_articles.id", ondelete="CASCADE"), nullable=False)
    availability: Mapped[str] = mapped_column(String(64))
    availability_code: Mapped[str] = mapped_column(String(32))
    document_style: Mapped[str] = mapped_column(String(32))
    site: Mapped[str] = mapped_column(String(64))
    url: Mapped[str] = mapped_column(Text)

    # Audit fields
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    deleted_by: Mapped[Optional[str]] = mapped_column(String(64))
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)
