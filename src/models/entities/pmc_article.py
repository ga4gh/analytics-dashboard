from datetime import datetime
from typing import List, Optional

from src.models.citation import Citation, Reference
from src.models.extras import FullText, Grant, Keyword
from src.models.pmc_author import PMCAffiliation, PMCAuthor, ArticleAuthor
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .pmc_author import PMCAffiliation, ArticleAuthor
from .extras import Keyword, Grant, FullText
from .citations import Citation, Reference

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    TIMESTAMP,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from .base import Base


class PMCArticle(Base):
    __tablename__ = "pmc_articles"

    # ---------- PK / FK ----------
    id: Mapped[int] = mapped_column(primary_key=True)
    record_id: Mapped[int] = mapped_column(
        ForeignKey("records.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ---------- Core fields ----------
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    pm_id: Mapped[Optional[str]] = mapped_column(String(64))
    pmc_id: Mapped[str] = mapped_column(String(64), nullable=False)
    full_text_id: Mapped[str] = mapped_column(String(128), nullable=False)
    doi: Mapped[str] = mapped_column(String(64), nullable=False)

    title: Mapped[str] = mapped_column(Text, nullable=False)
    pub_year: Mapped[int] = mapped_column(Integer, nullable=False)
    abstract_text: Mapped[str] = mapped_column(Text, nullable=False)
    affiliation: Mapped[str] = mapped_column(Text, nullable=False)
    publication_status: Mapped[str] = mapped_column(String(64), nullable=False)
    language: Mapped[str] = mapped_column(String(32), nullable=False)
    pub_type: Mapped[Optional[str]] = mapped_column(String(64))

    # ---------- Flags ----------
    is_open_access: Mapped[bool] = mapped_column(Boolean, default=False)
    inepmc: Mapped[bool] = mapped_column(Boolean, default=False)
    inpmc: Mapped[bool] = mapped_column(Boolean, default=False)
    has_pdf: Mapped[bool] = mapped_column(Boolean, default=False)
    has_book: Mapped[bool] = mapped_column(Boolean, default=False)
    has_suppl: Mapped[bool] = mapped_column(Boolean, default=False)

    cited_by_count: Mapped[int] = mapped_column(Integer, default=0)
    has_references: Mapped[bool] = mapped_column(Boolean, default=False)

    # ---------- Dates ----------
    date_of_creation: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )
    first_index_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )
    fulltext_receive_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )
    revision_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )
    epub_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )
    first_publication_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )

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

    # ---------- Relationships ----------
    article_authors: Mapped[List["ArticleAuthor"]] = relationship(
        cascade="all, delete-orphan",
        order_by="ArticleAuthor.author_order"
    )

    affiliations: Mapped[List["PMCAffiliation"]] = relationship(
        cascade="all, delete-orphan",
        order_by="PMCAffiliation.affiliation_order"
    )

    keywords: Mapped[List["Keyword"]] = relationship(
        cascade="all, delete-orphan"
    )

    grants: Mapped[List["Grant"]] = relationship(
        cascade="all, delete-orphan"
    )

    fulltexts: Mapped[List["FullText"]] = relationship(
        cascade="all, delete-orphan"
    )

    citations: Mapped[List["Citation"]] = relationship(
        cascade="all, delete-orphan"
    )

    references: Mapped[List["Reference"]] = relationship(
        cascade="all, delete-orphan"
    )
