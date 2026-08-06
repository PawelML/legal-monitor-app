"""Idempotent extraction of official PDFs into immutable text versions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, cast
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from legal_monitor.eli.client import Publisher
from legal_monitor.extraction.eli_pdf import DownloadedPdf
from legal_monitor.extraction.pdf import EXTRACTOR_VERSION, extract_pdf_text
from legal_monitor.models import Act, ActText, JobRun
from legal_monitor.services.ingestion import utc_now


class ActPdfSource(Protocol):
    """Download an act's official PDF without coupling the service to HTTP."""

    async def download(
        self, publisher: Publisher, year: int, position: int
    ) -> DownloadedPdf:
        """Return PDF bytes and their canonical source URL."""


@dataclass(frozen=True, slots=True)
class TextExtractionResult:
    """Observable result of one explicit source-text extraction."""

    job_run_id: str
    act_text_id: str
    created: bool


class TextExtractionService:
    """Persist a text version only after full, successful local extraction."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        source: ActPdfSource,
    ) -> None:
        self._session_factory = session_factory
        self._source = source

    async def extract(self, act_eli: str) -> TextExtractionResult:
        """Download and extract one known act, retaining a useful job record."""
        job_id = uuid4().hex
        async with self._session_factory() as session:
            session.add(
                JobRun(
                    id=job_id,
                    job_type="act_text_extraction",
                    status="running",
                    parameters={"act_eli": act_eli},
                    started_at=utc_now(),
                )
            )
            await session.commit()
            try:
                act = await session.get(Act, act_eli)
                if act is None:
                    raise ValueError(f"unknown act: {act_eli}")
                if not act.has_text_pdf:
                    raise ValueError(f"act has no official PDF: {act_eli}")
                pdf = await self._source.download(
                    cast(Publisher, act.publisher), act.year, act.position
                )
                extracted = extract_pdf_text(pdf.content)
                existing = await session.scalar(
                    select(ActText).where(
                        ActText.act_eli == act_eli,
                        ActText.content_hash == extracted.content_hash,
                    )
                )
                created = existing is None
                act_text = existing or ActText(
                    id=uuid4().hex,
                    act_eli=act_eli,
                    source_url=pdf.source_url,
                    extractor_version=EXTRACTOR_VERSION,
                    content_hash=extracted.content_hash,
                    content=extracted.content,
                    pages=extracted.pages,
                    created_at=utc_now(),
                )
                if created:
                    session.add(act_text)
                job = await session.get(JobRun, job_id)
                assert job is not None
                job.status = "succeeded"
                job.input_count = 1
                job.created_count = int(created)
                job.finished_at = utc_now()
                await session.commit()
            except Exception as exc:
                await session.rollback()
                job = await session.get(JobRun, job_id)
                assert job is not None
                job.status = "failed"
                job.error_summary = f"{type(exc).__name__}: {exc}"[:1000]
                job.finished_at = utc_now()
                await session.commit()
                raise
        return TextExtractionResult(job_id, act_text.id, created)
