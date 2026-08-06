"""Validated, grounded persistence of a provider's act analysis."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from legal_monitor.analysis.contracts import (
    AnalysisDraft,
    AnalysisOutput,
    Evidence,
    analysis_provenance,
    normalise_evidence_text,
    validate_evidence,
)
from legal_monitor.analysis.providers import AnalysisProvider, ProviderAnalysisResult
from legal_monitor.models import ActAnalysis, ActText, JobRun
from legal_monitor.services.ingestion import utc_now


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Observable result of one analysis attempt."""

    job_run_id: str
    analysis_id: str


@dataclass(frozen=True, slots=True)
class SourceChunk:
    """One deterministic, page-addressable segment of extracted source text."""

    chunk_id: str
    page: int
    text: str


def source_chunks(pages: list[str], maximum_characters: int = 450) -> list[SourceChunk]:
    """Split pages on word boundaries into stable chunks suitable for citation."""
    chunks: list[SourceChunk] = []
    for page_number, page in enumerate(pages, 1):
        words = normalise_evidence_text(page).split()
        current_words: list[str] = []
        chunk_number = 1
        for word in words:
            candidate = " ".join([*current_words, word])
            if current_words and len(candidate) > maximum_characters:
                chunks.append(
                    SourceChunk(
                        chunk_id=f"p{page_number}-c{chunk_number}",
                        page=page_number,
                        text=" ".join(current_words),
                    )
                )
                chunk_number += 1
                current_words = [word]
            else:
                current_words.append(word)
        if current_words:
            chunks.append(
                SourceChunk(
                    chunk_id=f"p{page_number}-c{chunk_number}",
                    page=page_number,
                    text=" ".join(current_words),
                )
            )
    return chunks


def chunk_marked_text(chunks: list[SourceChunk]) -> str:
    """Render source chunks without inviting the model to reproduce quotations."""
    return "\n\n".join(f"[{chunk.chunk_id}]\n{chunk.text}" for chunk in chunks)


def materialise_output(
    draft: AnalysisDraft, chunks: list[SourceChunk]
) -> AnalysisOutput:
    """Replace model-selected chunk IDs with exact persisted source quotations."""
    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    evidence: list[Evidence] = []
    for reference in draft.evidence:
        chunk = chunks_by_id.get(reference.chunk_id)
        if chunk is None:
            raise ValueError(f"unknown evidence chunk reference: {reference.chunk_id}")
        evidence.append(Evidence(page=chunk.page, quote=chunk.text))
    return AnalysisOutput(
        summary_pl=draft.summary_pl,
        business_relevant=draft.business_relevant,
        affected_parties=draft.affected_parties,
        tags=draft.tags,
        obligations=draft.obligations,
        effective_from=draft.effective_from,
        impact_level=draft.impact_level,
        evidence=evidence,
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
            request_started = perf_counter()
            provider_result: ProviderAnalysisResult | None = None
            try:
                text = await session.scalar(
                    select(ActText)
                    .where(ActText.act_eli == act_eli)
                    .order_by(ActText.created_at.desc())
                    .limit(1)
                )
                if text is None:
                    raise ValueError(f"no extracted text for act: {act_eli}")
                chunks = source_chunks(text.pages)
                provider_result = await self._provider.analyse(
                    chunk_marked_text(chunks), prompt_version
                )
                draft = AnalysisDraft.model_validate_json(provider_result.response_json)
                output = materialise_output(draft, chunks)
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
                job.parameters = {
                    **job.parameters,
                    "latency_ms": round((perf_counter() - request_started) * 1000),
                    "input_tokens": _input_tokens(provider_result),
                    "output_tokens": _output_tokens(provider_result),
                }
                job.finished_at = utc_now()
                await session.commit()
            except Exception as exc:
                await session.rollback()
                job = await session.get(JobRun, job_id)
                assert job is not None
                job.status = "failed"
                job.error_summary = f"{type(exc).__name__}: {exc}"[:1000]
                job.parameters = {
                    **job.parameters,
                    "latency_ms": round((perf_counter() - request_started) * 1000),
                    "input_tokens": _input_tokens(provider_result),
                    "output_tokens": _output_tokens(provider_result),
                }
                job.finished_at = utc_now()
                await session.commit()
                raise
        return AnalysisResult(job_id, analysis.id)


def _input_tokens(result: ProviderAnalysisResult | None) -> int | None:
    """Preserve API usage even when downstream schema validation rejects output."""
    return result.input_tokens if result is not None else None


def _output_tokens(result: ProviderAnalysisResult | None) -> int | None:
    """Preserve API usage even when downstream schema validation rejects output."""
    return result.output_tokens if result is not None else None
