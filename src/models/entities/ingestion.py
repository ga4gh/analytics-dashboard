from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Ingestion(Base):
    __tablename__ = "ingestion"

    # ---------- PK ----------
    id: Mapped[int] = mapped_column(primary_key=True)

    # ---------- Core fields ----------
    ingested_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )
    rows_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # ---------- Audit ----------
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    
