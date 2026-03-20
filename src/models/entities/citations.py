from datetime import datetime
from typing import List, Optional

from sqlalchemy import ForeignKey, Integer, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Citation(Base):
    __tablename__ = "citations"

    # ---------- PK / FK ----------
    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("pmc_articles.id", ondelete="CASCADE"), nullable=False)
    ingestion_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("ingestion.id", ondelete="SET NULL"),
    )

    # ---------- Core fields ----------
    citation_id: Mapped[str] = mapped_column(String(128))
    source: Mapped[str] = mapped_column(String(64))
    citation_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(Text)
    authors: Mapped[str] = mapped_column(Text)
    pub_year: Mapped[int] = mapped_column(Integer)
    citation_count: Mapped[int] = mapped_column(Integer, default=0)

    # ---------- Audit ----------
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    deleted_by: Mapped[Optional[str]] = mapped_column(String(64))
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)


class Reference(Base):
    __tablename__ = "pmc_references"

    # ---------- PK / FK ----------
    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("pmc_articles.id", ondelete="CASCADE"), nullable=False)
    ingestion_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("ingestion.id", ondelete="SET NULL"),
    )

    # ---------- Core fields ----------
    reference_id: Mapped[str] = mapped_column(String(128))
    source: Mapped[str] = mapped_column(String(64))
    citation_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(Text)
    authors: Mapped[str] = mapped_column(Text)
    pub_year: Mapped[int] = mapped_column(Integer)
    issn: Mapped[Optional[str]] = mapped_column(String(32))
    essn: Mapped[Optional[str]] = mapped_column(String(32))
    cited_order: Mapped[int] = mapped_column(Integer)
    match: Mapped[str] = mapped_column(String(8))

    # ---------- Audit ----------
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    deleted_by: Mapped[Optional[str]] = mapped_column(String(64))
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)
