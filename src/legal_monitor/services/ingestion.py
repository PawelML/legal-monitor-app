"""Idempotent service for importing ELI metadata."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from legal_monitor.eli.client import ELIActRecord, Publisher
from legal_monitor.models import Act, JobRun


class ELIActSource(Protocol):
    """Boundary that makes ELI transport replaceable in tests."""

    async def list_acts(self, publisher: Publisher, year: int) -> list[ELIActRecord]:
        """Return validated act records for one publisher and year."""


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Observable result of one import command."""

    job_run_id: str
    input_count: int
    created_count: int
    updated_count: int


def utc_now() -> datetime:
    """Return an aware UTC timestamp for persistence."""
    return datetime.now(UTC)


def _copy_record_to_act(act: Act, record: ELIActRecord) -> bool:
    """Copy source data and report whether an existing row changed."""
    fields = {
        "publisher": record.publisher,
        "year": record.year,
        "position": record.position,
        "address": record.address,
        "display_address": record.display_address,
        "title": record.title,
        "act_type": record.act_type,
        "status": record.status,
        "volume": record.volume,
        "announcement_date": record.announcement_date,
        "promulgation_date": record.promulgation_date,
        "source_change_date": record.change_date,
        "has_text_html": record.has_text_html,
        "has_text_pdf": record.has_text_pdf,
        "raw_metadata": record.raw_metadata,
    }
    changed = any(getattr(act, name) != value for name, value in fields.items())
    if changed:
        for name, value in fields.items():
            setattr(act, name, value)
        act.updated_at = utc_now()
    return changed


def _new_act(record: ELIActRecord) -> Act:
    """Create a persistent act from a validated source record."""
    now = utc_now()
    return Act(
        eli=record.eli,
        publisher=record.publisher,
        year=record.year,
        position=record.position,
        address=record.address,
        display_address=record.display_address,
        title=record.title,
        act_type=record.act_type,
        status=record.status,
        volume=record.volume,
        announcement_date=record.announcement_date,
        promulgation_date=record.promulgation_date,
        source_change_date=record.change_date,
        has_text_html=record.has_text_html,
        has_text_pdf=record.has_text_pdf,
        raw_metadata=record.raw_metadata,
        created_at=now,
        updated_at=now,
    )


class MetadataIngestionService:
    """Import annual metadata in one transaction after creating a job record."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        source: ELIActSource,
    ) -> None:
        self._session_factory = session_factory
        self._source = source

    async def import_year(
        self,
        year: int,
        publishers: tuple[Publisher, ...] = ("DU", "MP"),
    ) -> IngestionResult:
        """Fetch, upsert and record one explicit import attempt."""
        job_run_id = uuid4().hex
        parameters = {"year": year, "publishers": list(publishers)}
        async with self._session_factory() as session:
            session.add(
                JobRun(
                    id=job_run_id,
                    job_type="eli_metadata_import",
                    status="running",
                    parameters=parameters,
                    started_at=utc_now(),
                )
            )
            await session.commit()

            try:
                records = await self._fetch_records(year, publishers)
                created_count, updated_count = await self._upsert_records(
                    session, records
                )
                job_run = await session.get(JobRun, job_run_id)
                assert job_run is not None
                job_run.status = "succeeded"
                job_run.input_count = len(records)
                job_run.created_count = created_count
                job_run.updated_count = updated_count
                job_run.finished_at = utc_now()
                await session.commit()
            except Exception as exc:
                await session.rollback()
                job_run = await session.get(JobRun, job_run_id)
                assert job_run is not None
                job_run.status = "failed"
                job_run.error_summary = f"{type(exc).__name__}: {exc}"[:1000]
                job_run.finished_at = utc_now()
                await session.commit()
                raise

        return IngestionResult(
            job_run_id=job_run_id,
            input_count=len(records),
            created_count=created_count,
            updated_count=updated_count,
        )

    async def _fetch_records(
        self,
        year: int,
        publishers: tuple[Publisher, ...],
    ) -> list[ELIActRecord]:
        records: list[ELIActRecord] = []
        for publisher in publishers:
            records.extend(await self._source.list_acts(publisher, year))
        return records

    async def _upsert_records(
        self,
        session: AsyncSession,
        records: list[ELIActRecord],
    ) -> tuple[int, int]:
        created_count = 0
        updated_count = 0
        for record in records:
            act = await session.get(Act, record.eli)
            if act is None:
                session.add(_new_act(record))
                created_count += 1
            elif _copy_record_to_act(act, record):
                updated_count += 1
        return created_count, updated_count
