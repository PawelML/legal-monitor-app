"""KRS-backed company profiles with observable, idempotent refreshes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from legal_monitor.analysis.taxonomy import TAGS_V1
from legal_monitor.krs.client import KrsCompanyRecord
from legal_monitor.models import CompanyProfile, JobRun
from legal_monitor.services.ingestion import utc_now


@dataclass(frozen=True, slots=True)
class ProfileRefreshResult:
    """Observable result of one profile refresh."""

    job_run_id: str
    profile_id: str
    created: bool


class KrsRecordSource(Protocol):
    """The narrow KRS dependency needed by profile refreshes."""

    async def fetch_current_extract(self, krs_number: str) -> KrsCompanyRecord:
        """Return a typed current KRS record for a normalised identifier."""


def validate_monitoring_tags(tags: list[str]) -> list[str]:
    """Return a stable, unique taxonomy subset selected by the caller."""
    unknown_tags = set(tags).difference(TAGS_V1)
    if unknown_tags:
        raise ValueError(f"unknown monitoring tags: {sorted(unknown_tags)}")
    return sorted(set(tags))


class CompanyProfileService:
    """Persist one safe projection of a KRS company record."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        krs_client: KrsRecordSource,
    ) -> None:
        self._session_factory = session_factory
        self._krs_client = krs_client

    async def refresh_from_krs(
        self, krs_number: str, monitoring_tags: list[str]
    ) -> ProfileRefreshResult:
        """Fetch public KRS data, then create or refresh one profile."""
        tags = validate_monitoring_tags(monitoring_tags)
        job_id = uuid4().hex
        async with self._session_factory() as session:
            session.add(
                JobRun(
                    id=job_id,
                    job_type="profile_refresh",
                    status="running",
                    parameters={"krs_number": krs_number},
                    started_at=utc_now(),
                )
            )
            await session.commit()
            try:
                record = await self._krs_client.fetch_current_extract(krs_number)
                result = await self._upsert(session, record, tags)
                job = await session.get(JobRun, job_id)
                assert job is not None
                job.status = "succeeded"
                job.input_count = 1
                job.created_count = int(result.created)
                job.updated_count = int(not result.created)
                job.parameters = {"krs_number": record.krs_number}
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
        return ProfileRefreshResult(job_id, result.profile_id, result.created)

    async def get_profile(self, profile_id: str) -> CompanyProfile | None:
        """Return the stored profile without querying the external registry."""
        async with self._session_factory() as session:
            return await session.get(CompanyProfile, profile_id)

    async def _upsert(
        self,
        session: AsyncSession,
        record: KrsCompanyRecord,
        monitoring_tags: list[str],
    ) -> ProfileRefreshResult:
        profile = await session.scalar(
            select(CompanyProfile).where(CompanyProfile.krs_number == record.krs_number)
        )
        created = profile is None
        now = utc_now()
        if profile is None:
            profile = CompanyProfile(
                id=uuid4().hex,
                krs_number=record.krs_number,
                name=record.name,
                legal_form=record.legal_form,
                pkd_codes=record.pkd_codes,
                monitoring_tags=monitoring_tags,
                registry_updated_on=record.registry_updated_on,
                refreshed_at=now,
                created_at=now,
            )
            session.add(profile)
        else:
            profile.name = record.name
            profile.legal_form = record.legal_form
            profile.pkd_codes = record.pkd_codes
            profile.monitoring_tags = monitoring_tags
            profile.registry_updated_on = record.registry_updated_on
            profile.refreshed_at = now
        await session.flush()
        return ProfileRefreshResult("", profile.id, created)
