"""Behavior tests for idempotent metadata ingestion."""

from __future__ import annotations

from dataclasses import replace

from sqlalchemy import func, select

from legal_monitor.db import create_engine, create_session_factory
from legal_monitor.eli.client import ELIActPayload, ELIActRecord, Publisher
from legal_monitor.models import Act, JobRun
from legal_monitor.services.ingestion import MetadataIngestionService


def record(title: str = "Example act") -> ELIActRecord:
    """Build one valid source record without a network dependency."""
    return ELIActRecord.from_payload(
        ELIActPayload.model_validate(
            {
                "ELI": "DU/2026/946",
                "address": "WDU20260000946",
                "announcementDate": "2026-07-13",
                "changeDate": "2026-07-15T09:48:41",
                "displayAddress": "Dz.U. 2026 poz. 946",
                "pos": 946,
                "promulgation": "2026-07-14",
                "publisher": "DU",
                "status": "obowiązujący",
                "textHTML": False,
                "textPDF": True,
                "title": title,
                "type": "Rozporządzenie",
                "volume": 0,
                "year": 2026,
            }
        )
    )


class StubSource:
    """Mutable ELI source for deterministic service tests."""

    def __init__(self, records: list[ELIActRecord]) -> None:
        self.records = records
        self.failure: Exception | None = None

    async def list_acts(self, publisher: Publisher, year: int) -> list[ELIActRecord]:
        if self.failure is not None:
            raise self.failure
        return [item for item in self.records if item.publisher == publisher]


async def test_import_is_idempotent_and_updates_changed_metadata() -> None:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    session_factory = create_session_factory(engine)
    try:
        from legal_monitor.db import Base

        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        source = StubSource([record()])
        service = MetadataIngestionService(session_factory, source)

        first = await service.import_year(2026, ("DU",))
        second = await service.import_year(2026, ("DU",))
        source.records = [replace(record("Updated title"))]
        third = await service.import_year(2026, ("DU",))

        import_counts = (
            first.created_count,
            second.created_count,
            third.updated_count,
        )
        assert import_counts == (1, 0, 1)

        async with session_factory() as session:
            act_count = await session.scalar(select(func.count()).select_from(Act))
            job_count = await session.scalar(select(func.count()).select_from(JobRun))
            act = await session.get(Act, "DU/2026/946")

        assert act_count == 1
        assert job_count == 3
        assert act is not None
        assert act.title == "Updated title"
    finally:
        await engine.dispose()


async def test_failed_import_keeps_failed_job_record() -> None:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    session_factory = create_session_factory(engine)
    try:
        from legal_monitor.db import Base

        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        source = StubSource([])
        source.failure = RuntimeError("ELI is unavailable")
        service = MetadataIngestionService(session_factory, source)

        try:
            await service.import_year(2026, ("DU",))
        except RuntimeError as exc:
            assert str(exc) == "ELI is unavailable"
        else:
            raise AssertionError("expected the source failure to be raised")

        async with session_factory() as session:
            job_run = await session.scalar(select(JobRun))

        assert job_run is not None
        assert job_run.status == "failed"
        assert job_run.error_summary == "RuntimeError: ELI is unavailable"
    finally:
        await engine.dispose()
