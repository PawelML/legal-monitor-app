"""Profile refresh and deterministic preview integration tests."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from legal_monitor.db import Base, create_engine, create_session_factory
from legal_monitor.krs.client import KrsCompanyRecord, KrsNotFoundError
from legal_monitor.models import Act, ActAnalysis, CompanyProfile, JobRun
from legal_monitor.services.company_profiles import CompanyProfileService
from legal_monitor.services.ingestion import utc_now
from legal_monitor.services.matching import MatchingPreviewService


class FakeKrsClient:
    """Deterministic public-register substitute for profile-service tests."""

    def __init__(self) -> None:
        self.failure: Exception | None = None

    async def fetch_current_extract(self, krs_number: str) -> KrsCompanyRecord:
        del krs_number
        if self.failure is not None:
            raise self.failure
        return KrsCompanyRecord(
            krs_number="0000500605",
            name="Example sp. z o.o.",
            legal_form="SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
            pkd_codes=["61.10.Z"],
            registry_updated_on=None,
        )


async def profile_database() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Create an isolated schema with one analysed legal act."""
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    session_factory = create_session_factory(engine)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    now = utc_now()
    async with session_factory() as session:
        session.add_all(
            [
                Act(
                    eli="DU/2026/1",
                    publisher="DU",
                    year=2026,
                    position=1,
                    address="WDU20260000001",
                    display_address="Dz.U. 2026 poz. 1",
                    title="Transport act",
                    act_type="Ustawa",
                    status="obowiązujący",
                    volume=0,
                    has_text_html=False,
                    has_text_pdf=True,
                    raw_metadata={},
                    created_at=now,
                    updated_at=now,
                ),
                Act(
                    eli="DU/2026/2",
                    publisher="DU",
                    year=2026,
                    position=2,
                    address="WDU20260000002",
                    display_address="Dz.U. 2026 poz. 2",
                    title="Non-business act",
                    act_type="Ustawa",
                    status="obowiązujący",
                    volume=0,
                    has_text_html=False,
                    has_text_pdf=True,
                    raw_metadata={},
                    created_at=now,
                    updated_at=now,
                ),
                ActAnalysis(
                    id="analysis1",
                    act_eli="DU/2026/1",
                    act_text_id="text1",
                    schema_version="v2",
                    taxonomy_version="v1",
                    prompt_version="test",
                    model="test",
                    output={"business_relevant": True, "tags": ["transport"]},
                    created_at=now,
                ),
                ActAnalysis(
                    id="analysis2",
                    act_eli="DU/2026/2",
                    act_text_id="text2",
                    schema_version="v2",
                    taxonomy_version="v1",
                    prompt_version="test",
                    model="test",
                    output={"business_relevant": False, "tags": []},
                    created_at=now,
                ),
            ]
        )
        await session.commit()
    return engine, session_factory


async def test_refresh_is_idempotent_and_excludes_nip() -> None:
    """One KRS record creates one profile and observable refresh jobs."""
    engine, session_factory = await profile_database()
    try:
        service = CompanyProfileService(session_factory, FakeKrsClient())
        first = await service.refresh_from_krs("500605", ["transport"])
        second = await service.refresh_from_krs("0000500605", ["transport"])

        async with session_factory() as session:
            profile_count = await session.scalar(
                select(func.count()).select_from(CompanyProfile)
            )
            profile = await session.get(CompanyProfile, first.profile_id)
            jobs = (
                await session.scalars(
                    select(JobRun)
                    .where(JobRun.job_type == "profile_refresh")
                    .order_by(JobRun.started_at)
                )
            ).all()
        assert first.created is True
        assert second.created is False
        assert profile_count == 1
        assert profile is not None
        assert profile.pkd_codes == ["61.10.Z"]
        assert not hasattr(profile, "nip")
        assert [job.status for job in jobs] == ["succeeded", "succeeded"]
    finally:
        await engine.dispose()


async def test_failed_refresh_and_preview_are_observable_without_delivery() -> None:
    """Source failure records a job; preview returns only shared-tag analyses."""
    engine, session_factory = await profile_database()
    try:
        client = FakeKrsClient()
        service = CompanyProfileService(session_factory, client)
        client.failure = KrsNotFoundError("not found")
        try:
            await service.refresh_from_krs("500605", ["transport"])
        except KrsNotFoundError:
            pass
        else:
            raise AssertionError("expected KRS not found")
        client.failure = None
        profile = await service.refresh_from_krs("500605", ["transport"])
        preview = await MatchingPreviewService(session_factory).preview(
            profile.profile_id
        )
        repeated_preview = await MatchingPreviewService(session_factory).preview(
            profile.profile_id
        )

        async with session_factory() as session:
            failed_job = await session.scalar(
                select(JobRun).where(
                    JobRun.job_type == "profile_refresh", JobRun.status == "failed"
                )
            )
            preview_job = await session.get(JobRun, preview.job_run_id)
            repeated_preview_job = await session.get(
                JobRun, repeated_preview.job_run_id
            )
        assert failed_job is not None
        assert preview_job is not None
        assert repeated_preview_job is not None
        assert preview_job.status == "succeeded"
        assert repeated_preview_job.status == "succeeded"
        assert [(match.act_eli, match.shared_tags) for match in preview.matches] == [
            ("DU/2026/1", ["transport"])
        ]
    finally:
        await engine.dispose()
