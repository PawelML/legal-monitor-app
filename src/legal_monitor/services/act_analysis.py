"""Validated, grounded persistence of a provider's act analysis."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from legal_monitor.analysis.contracts import (
    AnalysisOutput,
    analysis_provenance,
    normalise_evidence_text,
    validate_evidence,
)
from legal_monitor.analysis.providers import AnalysisProvider
from legal_monitor.models import ActAnalysis, ActText, JobRun
from legal_monitor.services.ingestion import utc_now


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Observable result of one analysis attempt."""

    job_run_id: str
    analysis_id: str


def page_marked_text(pages: list[str]) -> str:
    """Preserve page provenance in the source text supplied to an analyser."""
    return "\n\n".join(
        f"[PAGE {page_number}]\n{normalise_evidence_text(page)}"
        for page_number, page in enumerate(pages, 1)
    )


class ActAnalysisService:
    """Create an analysis only after schema and source-grounding validation."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        provider: AnalysisProvider,
    ) -> None:
        self._session_factory = session_factory
        self._provider = provider

    async def analyse(self, act_eli: str, prompt_version: str) -> AnalysisResult:
        """Analyse the latest extracted text for one act."""
        job_id = uuid4().hex
        async with self._session_factory() as session:
            session.add(
                JobRun(
                    id=job_id,
                    job_type="act_analysis",
                    status="running",
                    parameters={
                        "act_eli": act_eli,
                        "prompt_version": prompt_version,
                        "model": self._provider.model_name,
                    },
                    started_at=utc_now(),
                )
            )
            await session.commit()
            try:
                text = await session.scalar(
                    select(ActText)
                    .where(ActText.act_eli == act_eli)
                    .order_by(ActText.created_at.desc())
                    .limit(1)
                )
                if text is None:
                    raise ValueError(f"no extracted text for act: {act_eli}")
                raw_response = await self._provider.analyse(
                    page_marked_text(text.pages), prompt_version
                )
                output = AnalysisOutput.model_validate_json(raw_response)
                validate_evidence(output, text.pages)
                schema_version, taxonomy_version = analysis_provenance()
                analysis = ActAnalysis(
                    id=uuid4().hex,
                    act_eli=act_eli,
                    act_text_id=text.id,
                    schema_version=schema_version,
                    taxonomy_version=taxonomy_version,
                    prompt_version=prompt_version,
                    model=self._provider.model_name,
                    output=output.model_dump(mode="json"),
                    created_at=utc_now(),
                )
                session.add(analysis)
                job = await session.get(JobRun, job_id)
                assert job is not None
                job.status = "succeeded"
                job.input_count = 1
                job.created_count = 1
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
        return AnalysisResult(job_id, analysis.id)
