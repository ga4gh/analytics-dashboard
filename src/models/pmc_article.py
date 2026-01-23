from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class PMCArticle(Base):
    __tablename__ = "pmc_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(Integer, nullable=False)

    source: Mapped[str] = mapped_column(String(100), nullable=False)
    pm_id: Mapped[Optional[str]] = mapped_column(String(50))
    pmc_id: Mapped[str] = mapped_column(String(50), nullable=False)
    full_text_id: Mapped[str] = mapped_column(String(50), nullable=False)
    doi: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    pub_year: Mapped[int] = mapped_column(Integer, nullable=False)
    abstract_text: Mapped[str] = mapped_column(Text, nullable=False)
    affiliation: Mapped[str] = mapped_column(Text, nullable=False)
    publicication_status: Mapped[str] = mapped_column(String(50), nullable=False)
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    pub_type: Mapped[Optional[str]] = mapped_column(String(100))

    is_open_access: Mapped[bool] = mapped_column(Boolean, default=False)
    inEPMC: Mapped[bool] = mapped_column(Boolean, default=False)
    inPMC: Mapped[bool] = mapped_column(Boolean, default=False)
    hasPDF: Mapped[bool] = mapped_column(Boolean, default=False)
    hasBook: Mapped[bool] = mapped_column(Boolean, default=False)
    hasSuppl: Mapped[bool] = mapped_column(Boolean, default=False)
    cited_by_count: Mapped[int] = mapped_column(Integer, default=0)
    has_references: Mapped[bool] = mapped_column(Boolean, default=False)

    dateofcreation: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    firstIndexdate: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fulltextreceivedate: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revisiondate: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    epubdate: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    firstpublicationdate: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships (examples)
    fulltexts: Mapped[List["PMCFullText"]] = relationship(
        back_populates="article", cascade="all, delete-orphan"
    )
    citations: Mapped[List["PMCCitation"]] = relationship(
        back_populates="article", cascade="all, delete-orphan"
    )
    references: Mapped[List["PMCReference"]] = relationship(
        back_populates="article", cascade="all, delete-orphan"
    )


class PMCFullText(Base):
    __tablename__ = "pmc_fulltexts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pmc_articles.id"))
    availability: Mapped[str] = mapped_column(String(100), nullable=False)
    availability_code: Mapped[str] = mapped_column(String(50), nullable=False)
    document_style: Mapped[str] = mapped_column(String(50), nullable=False)
    site: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)

    article: Mapped[Optional[PMCArticle]] = relationship(back_populates="fulltexts")


class PMCCitation(Base):
    __tablename__ = "pmc_citations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pmc_articles.id"))
    citation_id: Mapped[Optional[int]] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    citation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[str] = mapped_column(Text, nullable=False)
    pub_year: Mapped[int] = mapped_column(Integer, nullable=False)
    citation_count: Mapped[int] = mapped_column(Integer, default=0)

    article: Mapped[Optional[PMCArticle]] = relationship(back_populates="citations")


class PMCReference(Base):
    __tablename__ = "pmc_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pmc_articles.id"))
    reference_id: Mapped[Optional[int]] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    citation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[str] = mapped_column(Text, nullable=False)
    pub_year: Mapped[int] = mapped_column(Integer, nullable=False)
    issn: Mapped[str] = mapped_column(String(20), nullable=False)
    essn: Mapped[str] = mapped_column(String(20), nullable=False)
    cited_order: Mapped[int] = mapped_column(Integer, nullable=False)
    match: Mapped[str] = mapped_column(String(50), nullable=False)

    article: Mapped[Optional[PMCArticle]] = relationship(back_populates="references")

