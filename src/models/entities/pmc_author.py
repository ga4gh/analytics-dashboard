from datetime import datetime
from typing import List, Optional

from sqlalchemy import ForeignKey, Integer, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PMCAuthor(Base):
    __tablename__ = "pmc_authors"

    # ---------- PK ----------
    id: Mapped[int] = mapped_column(primary_key=True)

    # ---------- Core fields ----------
    fullname: Mapped[str] = mapped_column(Text, nullable=False)
    firstname: Mapped[Optional[str]] = mapped_column(String(128))
    lastname: Mapped[Optional[str]] = mapped_column(String(128))
    initials: Mapped[Optional[str]] = mapped_column(String(32))
    orcid: Mapped[Optional[str]] = mapped_column(String(64))

    # ---------- Audit ----------
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    deleted_by: Mapped[Optional[str]] = mapped_column(String(64))
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)

    # ---------- Relationships ----------
    # Links to affiliations (parent → child)
    affiliations: Mapped[List["PMCAffiliation"]] = relationship(
        cascade="all, delete-orphan",
        order_by="PMCAffiliation.affiliation_order"
    )

    # Links to article_authors (parent → child)
    article_links: Mapped[List["ArticleAuthor"]] = relationship(
        cascade="all, delete-orphan",
        order_by="ArticleAuthor.author_order"
    )


class PMCAffiliation(Base):
    __tablename__ = "pmc_affiliations"

    # ---------- PK / FK ----------
    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("pmc_authors.id", ondelete="CASCADE"), nullable=False)
    article_id: Mapped[int] = mapped_column(ForeignKey("pmc_articles.id", ondelete="CASCADE"), nullable=False)

    # ---------- Core fields ----------
    org_name: Mapped[Optional[str]] = mapped_column(Text)
    affiliation_order: Mapped[int] = mapped_column(Integer, nullable=False)

    # ---------- Audit ----------
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    deleted_by: Mapped[Optional[str]] = mapped_column(String(64))
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)


class ArticleAuthor(Base):
    __tablename__ = "articles_authors"

    # ---------- PK / FK ----------
    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("pmc_articles.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("pmc_authors.id", ondelete="CASCADE"), nullable=False)

    # ---------- Order ----------
    author_order: Mapped[Optional[int]] = mapped_column(Integer)

    # ---------- Audit ----------
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    deleted_by: Mapped[Optional[str]] = mapped_column(String(64))
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)
