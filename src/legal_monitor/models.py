"""Persistence models for Phase 0 ingestion."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from legal_monitor.db import Base


class Act(Base):
    """One official legal act, uniquely identified by its ELI identifier."""

    __tablename__ = "acts"

    eli: Mapped[str] = mapped_column(String(64), primary_key=True)
    publisher: Mapped[str] = mapped_column(String(2), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    position: Mapped[int] = mapped_column(Integer)
    address: Mapped[str] = mapped_column(String(64))
    display_address: Mapped[str] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(Text)
    act_type: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(128))
    volume: Mapped[int] = mapped_column(Integer)
    announcement_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    promulgation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_change_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    has_text_html: Mapped[bool] = mapped_column(default=False)
    has_text_pdf: Mapped[bool] = mapped_column(default=False)
    raw_metadata: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class JobRun(Base):
    """Operational evidence for one metadata import attempt."""

    __tablename__ = "job_runs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    job_type: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(16), index=True)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON)
    input_count: Mapped[int] = mapped_column(Integer, default=0)
    created_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, default=0)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
