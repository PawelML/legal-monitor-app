"""Deterministic, non-deliverable matching previews for company profiles."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from legal_monitor.models import Act, ActAnalysis, CompanyProfile, JobRun
from legal_monitor.services.ingestion import utc_now


@dataclass(frozen=True, slots=True)
class PreviewMatch:
    """One explainable match with no score or alert semantics."""

    act_eli: str
    act_title: str
    analysis_id: str
    shared_tags: list[str]


@dataclass(frozen=True, slots=True)
class MatchingPreviewResult:
    """One observed preview run and its transient match items."""

    job_run_id: str
    matches: list[PreviewMatch]


class MatchingPreviewService:
    """Find shared taxonomy tags against each act's latest analysis."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def preview(self, profile_id: str) -> MatchingPreviewResult:
        """Create an observable transient preview without delivery side effects."""
        job_id = uuid4().hex
        async with self._session_factory() as session:
            session.add(
                JobRun(
                    id=job_id,
                    job_type="matching_preview",
                    status="running",
                    parameters={"profile_id": profile_id},
                    started_at=utc_now(),
                )
            )
            await session.commit()
            try:
                profile = await session.get(CompanyProfile, profile_id)
                if profile is None:
                    raise ValueError(f"profile not found: {profile_id}")
                matches = await self._matches(session, profile)
                job = await session.get(JobRun, job_id)
                assert job is not None
                job.status = "succeeded"
                job.input_count = len(profile.monitoring_tags)
                job.created_count = len(matches)
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
        return MatchingPreviewResult(job_id, matches)

    async def _matches(
        self, session: AsyncSession, profile: CompanyProfile
    ) -> list[PreviewMatch]:
        rows = (
            await session.execute(
                select(ActAnalysis, Act)
                .join(Act, Act.eli == ActAnalysis.act_eli)
                .order_by(ActAnalysis.act_eli, ActAnalysis.created_at.desc())
            )
        ).all()
        profile_tags = set(profile.monitoring_tags)
        seen_act_eli: set[str] = set()
        matches: list[PreviewMatch] = []
        for analysis, act in rows:
            if analysis.act_eli in seen_act_eli:
                continue
            seen_act_eli.add(analysis.act_eli)
            output = analysis.output
            if output.get("business_relevant") is not True:
                continue
            output_tags = output.get("tags")
            if not isinstance(output_tags, list):
                continue
            shared_tags = sorted(profile_tags.intersection(output_tags))
            if shared_tags:
                matches.append(
                    PreviewMatch(
                        act_eli=analysis.act_eli,
                        act_title=act.title,
                        analysis_id=analysis.id,
                        shared_tags=shared_tags,
                    )
                )
        return matches
