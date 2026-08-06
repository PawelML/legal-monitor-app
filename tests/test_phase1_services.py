"""Phase 1 persistence, grounding and failure-regression tests."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from legal_monitor.analysis.providers import StaticAnalysisProvider
from legal_monitor.db import Base, create_engine, create_session_factory
from legal_monitor.extraction.eli_pdf import DownloadedPdf
from legal_monitor.extraction.pdf import ExtractedPdfText
from legal_monitor.models import Act, ActAnalysis, ActText, JobRun
from legal_monitor.services.act_analysis import ActAnalysisService
from legal_monitor.services.ingestion import utc_now
from legal_monitor.services.text_extraction import TextExtractionService


class StubPdfSource:
    """A deterministic official-PDF substitute for integration tests."""

    def __init__(self) -> None:
        self.failure: Exception | None = None

    async def download(self, publisher: str, year: int, position: int) -> DownloadedPdf:
        assert (publisher, year, position) == ("DU", 2026, 946)
        if self.failure is not None:
            raise self.failure
        return DownloadedPdf("https://example.test/act.pdf", b"not-a-real-pdf")


async def create_database() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Create the smallest database containing one PDF-backed act."""
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    session_factory = create_session_factory(engine)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with session_factory() as session:
        now = utc_now()
        session.add(
            Act(
                eli="DU/2026/946",
                publisher="DU",
                year=2026,
                position=946,
                address="WDU20260000946",
                display_address="Dz.U. 2026 poz. 946",
                title="Example act",
                act_type="Rozporządzenie",
                status="obowiązujący",
                volume=0,
                has_text_html=False,
                has_text_pdf=True,
                raw_metadata={},
                created_at=now,
                updated_at=now,
            )
        )
        await session.commit()
    return engine, session_factory


async def test_extraction_is_idempotent_and_preserves_source_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine, session_factory = await create_database()
    try:
        monkeypatch.setattr(
            "legal_monitor.services.text_extraction.extract_pdf_text",
            lambda _: ExtractedPdfText(
                pages=["Przepis dotyczy podatku VAT."],
                content="Przepis dotyczy podatku VAT.",
                content_hash="a" * 64,
            ),
        )
        service = TextExtractionService(session_factory, StubPdfSource())

        first = await service.extract("DU/2026/946")
        second = await service.extract("DU/2026/946")

        assert first.created is True
        assert second.created is False
        assert first.act_text_id == second.act_text_id
        async with session_factory() as session:
            text_count = await session.scalar(select(func.count()).select_from(ActText))
            jobs = (
                await session.scalars(select(JobRun).order_by(JobRun.started_at))
            ).all()
        assert text_count == 1
        assert [job.status for job in jobs] == ["succeeded", "succeeded"]
    finally:
        await engine.dispose()


async def test_invalid_grounding_leaves_no_analysis_and_failed_job() -> None:
    engine, session_factory = await create_database()
    try:
        async with session_factory() as session:
            session.add(
                ActText(
                    id="text1",
                    act_eli="DU/2026/946",
                    source_url="https://example.test/act.pdf",
                    extractor_version="test",
                    content_hash="b" * 64,
                    content="Przepis dotyczy podatku VAT.",
                    pages=["Przepis dotyczy podatku VAT."],
                    created_at=utc_now(),
                )
            )
            await session.commit()
        response = json.dumps(
            {
                "summary_pl": "Przepis wprowadza obowiązek dla podatników VAT.",
                "business_relevant": True,
                "affected_parties": ["podatnicy VAT"],
                "tags": ["taxes_vat"],
                "obligations": ["Złożyć deklarację."],
                "effective_from": "2026-07-20",
                "impact_level": 3,
                "evidence": [{"page": 1, "quote": "Nieistniejący cytat"}],
            }
        )
        service = ActAnalysisService(session_factory, StaticAnalysisProvider(response))

        with pytest.raises(ValueError, match="evidence quote"):
            await service.analyse("DU/2026/946", "v1")

        async with session_factory() as session:
            count = await session.scalar(select(func.count()).select_from(ActAnalysis))
            job = await session.scalar(
                select(JobRun).where(JobRun.job_type == "act_analysis")
            )
        assert count == 0
        assert job is not None
        assert job.status == "failed"
    finally:
        await engine.dispose()


async def test_valid_analysis_persists_versions_and_output() -> None:
    engine, session_factory = await create_database()
    try:
        async with session_factory() as session:
            session.add(
                ActText(
                    id="text2",
                    act_eli="DU/2026/946",
                    source_url="https://example.test/act.pdf",
                    extractor_version="test",
                    content_hash="c" * 64,
                    content="Przepis dotyczy podatku VAT.",
                    pages=["Przepis dotyczy podatku VAT."],
                    created_at=utc_now(),
                )
            )
            await session.commit()
        response = json.dumps(
            {
                "summary_pl": "Przepis dotyczy obowiązków podatników VAT.",
                "business_relevant": True,
                "affected_parties": ["podatnicy VAT"],
                "tags": ["taxes_vat"],
                "obligations": ["Sprawdzić deklarację VAT."],
                "effective_from": None,
                "impact_level": 2,
                "evidence": [{"page": 1, "quote": "Przepis dotyczy podatku VAT."}],
            }
        )
        result = await ActAnalysisService(
            session_factory, StaticAnalysisProvider(response)
        ).analyse("DU/2026/946", "v1")

        async with session_factory() as session:
            analysis = await session.get(ActAnalysis, result.analysis_id)
        assert analysis is not None
        assert analysis.schema_version == "v1"
        assert analysis.taxonomy_version == "v1"
        assert analysis.output["tags"] == ["taxes_vat"]
    finally:
        await engine.dispose()
